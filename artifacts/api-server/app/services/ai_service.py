"""
AI Service — orchestrates multiple providers with intelligent failover,
load balancing by priority/availability, and request routing.
"""
from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from app.config import settings
from app.services.providers.base import BaseProvider, ImageResult, ProviderResult

if TYPE_CHECKING:
    pass

# ──────────────────────────────────────────────
# Model registry
# ──────────────────────────────────────────────
_MODEL_REGISTRY: list[dict] = [
    {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "openai",
        "speed": "fast",
        "status": "active",
        "priority": 1,
        "max_tokens": 16384,
        "supports_images": False,
    },
    {
        "id": "gpt-4.1-mini",
        "name": "GPT-4.1 Mini",
        "provider": "openai",
        "speed": "fast",
        "status": "active",
        "priority": 2,
        "max_tokens": 8192,
        "supports_images": False,
    },
    {
        "id": "gpt-4.1-nano",
        "name": "GPT-4.1 Nano",
        "provider": "openai",
        "speed": "fast",
        "status": "active",
        "priority": 3,
        "max_tokens": 8192,
        "supports_images": False,
    },
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B",
        "provider": "groq",
        "speed": "fast",
        "status": "active",
        "priority": 4,
        "max_tokens": 8192,
        "supports_images": False,
    },
    {
        "id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B Instant",
        "provider": "groq",
        "speed": "fast",
        "status": "active",
        "priority": 5,
        "max_tokens": 8192,
        "supports_images": False,
    },
    {
        "id": "mixtral-8x7b-32768",
        "name": "Mixtral 8x7B",
        "provider": "groq",
        "speed": "fast",
        "status": "active",
        "priority": 6,
        "max_tokens": 32768,
        "supports_images": False,
    },
    {
        "id": "dall-e-3",
        "name": "DALL-E 3",
        "provider": "openai",
        "speed": "medium",
        "status": "active",
        "priority": 1,
        "max_tokens": 0,
        "supports_images": True,
    },
]

# Runtime status overrides (can be changed via admin)
_model_status_overrides: dict[str, str] = {}
_model_latency: dict[str, int] = {}


def get_all_models() -> list[dict]:
    result = []
    for m in _MODEL_REGISTRY:
        entry = dict(m)
        entry["status"] = _model_status_overrides.get(m["id"], m["status"])
        entry["latencyMs"] = _model_latency.get(m["id"])
        result.append(entry)
    return result


def update_model_status(model_id: str, status: str, priority: int | None = None):
    _model_status_overrides[model_id] = status
    for m in _MODEL_REGISTRY:
        if m["id"] == model_id:
            if priority is not None:
                m["priority"] = priority
            break


# ──────────────────────────────────────────────
# Provider pool
# ──────────────────────────────────────────────
_chat_providers: list[BaseProvider] = []
_image_providers: list[BaseProvider] = []


def _build_providers():
    global _chat_providers, _image_providers
    from app.services.providers.openai_provider import OpenAIProvider
    from app.services.providers.groq_provider import GroqProvider

    _chat_providers = []
    _image_providers = []

    if settings.openai_api_key:
        openai = OpenAIProvider(api_key=settings.openai_api_key)
        openai.priority = 1
        _chat_providers.append(openai)
        _image_providers.append(openai)

    if settings.groq_api_key:
        groq = GroqProvider(api_key=settings.groq_api_key)
        groq.priority = 2
        _chat_providers.append(groq)

    # Sort by priority
    _chat_providers.sort(key=lambda p: p.priority)
    _image_providers.sort(key=lambda p: p.priority)


_build_providers()


def _provider_for_model(model_id: str | None, providers: list[BaseProvider]) -> list[BaseProvider]:
    """Return the list of providers sorted by priority for the requested model."""
    if not model_id:
        return [p for p in providers if p.is_available()]

    # Find the preferred provider for this model
    preferred_provider_id: str | None = None
    for m in _MODEL_REGISTRY:
        if m["id"] == model_id:
            preferred_provider_id = m["provider"]
            break

    # Sort: preferred first, then others as fallback
    sorted_providers = sorted(
        [p for p in providers if p.is_available()],
        key=lambda p: (0 if p.provider_id == preferred_provider_id else 1, p.priority),
    )
    return sorted_providers


def _resolve_model_for_provider(provider: BaseProvider, requested_model: str | None) -> str:
    """Pick the best model ID for a given provider."""
    if requested_model:
        # Check if provider supports this model
        for m in _MODEL_REGISTRY:
            if m["id"] == requested_model and m["provider"] == provider.provider_id:
                return requested_model
    # Fall back to provider's default model
    defaults = {
        "openai": "gpt-4o-mini",
        "groq": "llama-3.3-70b-versatile",
    }
    return defaults.get(provider.provider_id, "gpt-4o-mini")


async def chat_with_failover(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> tuple[ProviderResult, int]:
    """
    Run chat completion with intelligent failover.
    Returns (result, failover_count).
    """
    providers = _provider_for_model(model, _chat_providers)
    if not providers:
        raise RuntimeError("No chat providers are available")

    errors: list[str] = []
    failover_count = 0

    for provider in providers:
        resolved_model = _resolve_model_for_provider(provider, model)
        try:
            result = await asyncio.wait_for(
                provider.chat(
                    messages=messages,
                    model=resolved_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=settings.provider_timeout,
                ),
                timeout=settings.provider_timeout + 5,
            )
            _model_latency[resolved_model] = result.latency_ms or 0
            return result, failover_count
        except Exception as e:
            provider.mark_failed()
            errors.append(f"{provider.name}: {e}")
            failover_count += 1

    raise RuntimeError(f"All providers failed: {'; '.join(errors)}")


async def image_with_failover(
    prompt: str,
    size: str = "1024x1024",
    response_format: str = "url",
) -> tuple[ImageResult, int]:
    """
    Run image generation with failover.
    Returns (result, failover_count).
    """
    providers = [p for p in _image_providers if p.is_available()]
    if not providers:
        raise RuntimeError("No image providers are available")

    errors: list[str] = []
    failover_count = 0

    for provider in providers:
        try:
            result = await asyncio.wait_for(
                provider.generate_image(
                    prompt=prompt,
                    size=size,
                    response_format=response_format,
                ),
                timeout=90,
            )
            return result, failover_count
        except NotImplementedError:
            failover_count += 1
            continue
        except Exception as e:
            provider.mark_failed()
            errors.append(f"{provider.name}: {e}")
            failover_count += 1

    raise RuntimeError(f"All image providers failed: {'; '.join(errors)}")
