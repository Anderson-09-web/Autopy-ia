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
        model: str | None = None,
        timeout: float = 60.0,
    ) -> ImageResult:
        start = time.time()
        client = self._get_client()

        # Normalize size — dall-e-3 only accepts these three values.
        valid_sizes = {"1024x1024", "1024x1792", "1792x1024"}
        if size not in valid_sizes:
            size = "1024x1024"

        # Build the model priority list.
        # If the caller requests a specific model, start there; otherwise try dall-e-3 first.
        if model and model in ("dall-e-3", "dall-e-2"):
            models_to_try = [model, "dall-e-2"] if model == "dall-e-3" else [model, "dall-e-3"]
        else:
            models_to_try = ["dall-e-3", "dall-e-2"]

        last_error: Exception | None = None
        for m in models_to_try:
            try:
                kwargs: dict = dict(
                    model=m,
                    prompt=prompt,
                    n=1,
                    size=size,
                    response_format=response_format,  # "url" or "b64_json"
                )
                # dall-e-2 doesn't support 1024x1792 / 1792x1024
                if m == "dall-e-2" and size != "1024x1024":
                    kwargs["size"] = "1024x1024"
                response = await client.images.generate(**kwargs)
                latency_ms = int((time.time() - start) * 1000)
                img = response.data[0]
                self.mark_success()
                return ImageResult(
                    url=getattr(img, "url", None),
                    base64=getattr(img, "b64_json", None),
                    model=m,
                    provider=self.provider_id,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                last_error = e
                # Prompt / content policy errors are final — don't retry with another model.
                err_str = str(e).lower()
                if any(k in err_str for k in ("content_policy", "safety", "rejected", "invalid_image")):
                    raise
                # Any other error (quota, permission, model unavailable…) → try next model.
                continue

        raise last_error or RuntimeError("Image generation failed on all available models")
