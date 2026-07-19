"""
Abstract base class for all AI providers.
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderResult:
    text: str
    model: str
    provider: str
    tokens_used: int | None = None
    latency_ms: int | None = None


@dataclass
class ImageResult:
    url: str | None
    base64: str | None
    model: str
    provider: str
    latency_ms: int | None = None


class BaseProvider(ABC):
    """Abstract AI provider."""

    name: str = "base"
    provider_id: str = "base"
    priority: int = 999
    _failed_until: float = 0
    _backoff_seconds: float = 30.0

    def is_available(self) -> bool:
        """Return True if the provider is not in backoff."""
        return time.time() > self._failed_until

    def mark_failed(self):
        """Mark provider as failed, backing off for _backoff_seconds."""
        self._failed_until = time.time() + self._backoff_seconds

    def mark_success(self):
        """Reset backoff after successful response."""
        self._failed_until = 0

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 30.0,
    ) -> ProviderResult:
        """Generate a chat completion."""
        ...

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        response_format: str = "url",
        timeout: float = 60.0,
    ) -> ImageResult:
        """Generate an image. Override in providers that support it."""
        raise NotImplementedError(f"{self.name} does not support image generation")
