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
    # ── Chat: Groq (ultra-fast inference) ───────
    # Models are tried in order inside GroqProvider with per-model rate-limit backoff.
    {
        "id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B Instant",
        "provider": "groq",
        "speed": "fast",
        "status": "active",
        "priority": 1,
        "max_tokens": 8192,
        "supports_images": False,
    },
    {
        "id": "llama3-8b-8192",
        "name": "Llama 3 8B",
        "provider": "groq",
        "speed": "fast",
        "status": "active",
        "priority": 2,
        "max_tokens": 8192,
        "supports_images": False,
    },
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B",
        "provider": "groq",
        "speed": "fast",
        "status": "active",
        "priority": 3,
        "max_tokens": 32768,
        "supports_images": False,
    },
    # ── Images: Pollinations (free, no key needed) ──
    {
        "id": "flux",
        "name": "Flux (Pollinations)",
        "provider": "pollinations",
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
    from app.services.providers.groq_provider import GroqProvider
    from app.services.providers.pollinations_provider import PollinationsProvider

    _chat_providers = []
    _image_providers = []

    # Groq — chat, handles per-model rate-limit backoff internally
    if settings.groq_api_key:
        groq = GroqProvider(api_key=settings.groq_api_key)
        groq.priority = 1
        _chat_providers.append(groq)

    # Pollinations — images only, always available (no key needed)
    pollinations = PollinationsProvider()
    pollinations.priority = 1
    _image_providers.append(pollinations)

    _chat_providers.sort(key=lambda p: p.priority)
    _image_providers.sort(key=lambda p: p.priority)


_build_providers()


def _provider_for_model(model_id: str | None, providers: list[BaseProvider]) -> list[BaseProvider]:
    """Return providers sorted by priority for the requested model."""
    if not model_id:
        return [p for p in providers if p.is_available()]

    preferred_provider_id: str | None = None
    for m in _MODEL_REGISTRY:
        if m["id"] == model_id:
            preferred_provider_id = m["provider"]
            break

    sorted_providers = sorted(
        [p for p in providers if p.is_available()],
        key=lambda p: (0 if p.provider_id == preferred_provider_id else 1, p.priority),
    )
    return sorted_providers


def _resolve_model_for_provider(provider: BaseProvider, requested_model: str | None) -> str:
    """Pick the best model ID for a given provider."""
    if requested_model:
        for m in _MODEL_REGISTRY:
            if m["id"] == requested_model and m["provider"] == provider.provider_id:
                return requested_model
    defaults = {
        "groq": "llama-3.1-8b-instant",
    }
    return defaults.get(provider.provider_id, "llama-3.1-8b-instant")


async def chat_with_failover(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> tuple[ProviderResult, int]:
    """
    Run chat completion with intelligent failover.
    Uses failover_timeout for all but the last provider so we switch quickly
    when a provider hangs instead of waiting the full timeout.
    Returns (result, failover_count).
    """
    providers = _provider_for_model(model, _chat_providers)
    if not providers:
        # All providers are in backoff — try them anyway sorted by soonest to recover.
        all_providers = sorted(_chat_providers, key=lambda p: p.seconds_until_available())
        if not all_providers:
            raise RuntimeError("No chat providers are configured")
        providers = all_providers

    errors: list[str] = []
    failover_count = 0
    total = len(providers)

    for i, provider in enumerate(providers):
        is_last = i == total - 1
        # Use short failover_timeout for non-last providers so we switch fast.
        timeout = settings.provider_timeout if is_last else settings.failover_timeout
        resolved_model = _resolve_model_for_provider(provider, model)
        try:
            result = await asyncio.wait_for(
                provider.chat(
                    messages=messages,
                    model=resolved_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                ),
                timeout=timeout + 3,
            )
            _model_latency[resolved_model] = result.latency_ms or 0
            return result, failover_count
        except asyncio.TimeoutError:
            # Timeout — provider didn't self-mark, so we do it here.
            provider.mark_failed()
            errors.append(f"{provider.name}: timeout after {timeout}s")
            failover_count += 1
        except Exception as e:
            # Provider may have already called mark_rate_limited() or mark_failed()
            # internally. Only mark failed here if it didn't set a backoff itself.
            if provider.is_available():
                provider.mark_failed()
            errors.append(f"{provider.name}: {e}")
            failover_count += 1

    raise RuntimeError(f"All providers failed: {'; '.join(errors)}")


async def image_with_failover(
    prompt: str,
    size: str = "1024x1024",
    response_format: str = "url",
    model: str | None = None,
) -> tuple[ImageResult, int]:
    """
    Run image generation with failover.
    Always has Pollinations as the last-resort free fallback.
    Returns (result, failover_count).
    """
    providers = [p for p in _image_providers if p.is_available()]
    if not providers:
        raise RuntimeError("No image providers are available")

    errors: list[str] = []
    failover_count = 0
    total = len(providers)

    for i, provider in enumerate(providers):
        is_last = i == total - 1
        timeout = 90.0 if is_last else 60.0
        try:
            result = await asyncio.wait_for(
                provider.generate_image(
                    prompt=prompt,
                    size=size,
                    response_format=response_format,
                    model=model,
                ),
                timeout=timeout + 5,
            )
            return result, failover_count
        except NotImplementedError:
            failover_count += 1
            continue
        except Exception as e:
            err_str = str(e).lower()
            is_transient = any(
                k in err_str
                for k in ("timeout", "connection", "502", "503", "504", "rate_limit", "rate limit", "overloaded")
            )
            if is_transient:
                provider.mark_failed()
            errors.append(f"{provider.name}: {e}")
            failover_count += 1

    raise RuntimeError(f"All image providers failed: {'; '.join(errors)}")
