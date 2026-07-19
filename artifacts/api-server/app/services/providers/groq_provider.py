"""
Groq provider — ultra-fast inference via Groq API.
"""
import time

from app.services.providers.base import BaseProvider, ProviderResult


class GroqProvider(BaseProvider):
    name = "Groq"
    provider_id = "groq"
    priority = 2

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    async def chat(
        self,
        messages: list[dict],
        model: str = "llama-3.3-70b-versatile",
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
