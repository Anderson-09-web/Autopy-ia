"""
OpenAI provider — supports chat completions and image generation (DALL-E).
"""
import time

from app.services.providers.base import BaseProvider, ImageResult, ProviderResult


class OpenAIProvider(BaseProvider):
    name = "OpenAI"
    provider_id = "openai"
    priority = 1

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def chat(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 30.0,
    ) -> ProviderResult:
        start = time.time()
        client = self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
        latency_ms = int((time.time() - start) * 1000)
        text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else None
        self.mark_success()
        return ProviderResult(
            text=text,
            model=response.model,
            provider=self.provider_id,
            tokens_used=tokens,
            latency_ms=latency_ms,
        )

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        response_format: str = "url",
        timeout: float = 60.0,
    ) -> ImageResult:
        start = time.time()
        client = self._get_client()
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            response_format=response_format,
            n=1,
        )
        latency_ms = int((time.time() - start) * 1000)
        img = response.data[0]
        self.mark_success()
        return ImageResult(
            url=img.url if response_format == "url" else None,
            base64=img.b64_json if response_format == "b64_json" else None,
            model="dall-e-3",
            provider=self.provider_id,
            latency_ms=latency_ms,
        )
