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
            # Force base_url so env vars like OPENAI_BASE_URL can't redirect
            # requests to a wrong host (e.g. a Replit dev-domain proxy).
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.openai.com/v1",
            )
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

        # Normalize size — dall-e-3 only accepts these three values.
        valid_sizes = {"1024x1024", "1024x1792", "1792x1024"}
        if size not in valid_sizes:
            size = "1024x1024"

        # Try dall-e-3 first (broadly available), fall back to dall-e-2.
        for model in ("dall-e-3", "dall-e-2"):
            try:
                kwargs: dict = dict(
                    model=model,
                    prompt=prompt,
                    n=1,
                    size=size,
                    response_format=response_format,  # "url" or "b64_json"
                )
                # dall-e-2 doesn't support 1024x1792 / 1792x1024
                if model == "dall-e-2" and size != "1024x1024":
                    kwargs["size"] = "1024x1024"
                response = await client.images.generate(**kwargs)
                latency_ms = int((time.time() - start) * 1000)
                img = response.data[0]
                self.mark_success()
                return ImageResult(
                    url=getattr(img, "url", None),
                    base64=getattr(img, "b64_json", None),
                    model=model,
                    provider=self.provider_id,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                err_str = str(e).lower()
                # Only fall back on quota/access errors, not prompt errors
                if model == "dall-e-3" and any(
                    k in err_str for k in ("billing", "quota", "limit", "access", "permission", "not supported", "maximum")
                ):
                    continue
                raise
        raise RuntimeError("Image generation failed on all available models")
