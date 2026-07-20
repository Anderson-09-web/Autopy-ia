"""
Pollinations.AI provider — completely free image generation, no API key required.
Uses the Flux model. Acts as the last-resort fallback for image generation.
"""
import base64
import time
import urllib.parse

import httpx

from app.services.providers.base import BaseProvider, ImageResult, ProviderResult


class PollinationsProvider(BaseProvider):
    name = "Pollinations"
    provider_id = "pollinations"
    priority = 99  # last resort

    # No API key needed
    def __init__(self):
        super().__init__()

    async def chat(
        self,
        messages: list[dict],
        model: str = "openai",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 30.0,
    ) -> ProviderResult:
        raise NotImplementedError("Pollinations is image-only")

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        response_format: str = "url",
        model: str | None = None,
        timeout: float = 90.0,
    ) -> ImageResult:
        """
        Generate an image via Pollinations.AI (Flux model, free).
        Downloads the image and returns it as a base64 data-URL so the
        frontend can display it without CORS issues.
        """
        start = time.time()

        # Parse width/height
        parts = size.split("x") if "x" in size else ["1024", "1024"]
        try:
            w, h = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            w, h = 1024, 1024

        # Cap to supported sizes
        w = min(w, 1440)
        h = min(h, 1440)

        encoded_prompt = urllib.parse.quote(prompt, safe="")
        seed = int(time.time()) % 999999
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={w}&height={h}&nologo=true&model=flux&seed={seed}&enhance=true"
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "AutopyAI/1.0"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "image/jpeg")
        if "image" not in content_type:
            raise RuntimeError(f"Pollinations returned non-image content: {content_type}")

        latency_ms = int((time.time() - start) * 1000)
        mime = content_type.split(";")[0].strip()
        b64 = base64.b64encode(resp.content).decode("ascii")
        data_url = f"data:{mime};base64,{b64}"

        self.mark_success()
        return ImageResult(
            url=data_url,
            base64=b64,
            model="flux",
            provider=self.provider_id,
            latency_ms=latency_ms,
        )
