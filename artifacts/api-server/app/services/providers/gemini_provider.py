"""
Google Gemini provider — chat completions via REST API using httpx.
Supports: gemini-2.5-flash (default), gemini-2.5-pro, gemini-2.0-flash.
"""
import time

import httpx

from app.services.providers.base import BaseProvider, ImageResult, ProviderResult

_GEMINI_BASE = "https://generativelanguage.googleapis.com"


class GeminiProvider(BaseProvider):
    name = "Gemini"
    provider_id = "gemini"
    priority = 3

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _convert_messages(self, messages: list[dict]) -> tuple[list, list | None]:
        """Convert OpenAI-format messages → Gemini contents + system parts."""
        system_parts: list[dict] = []
        contents: list[dict] = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system_parts.append({"text": content})
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        return contents, system_parts if system_parts else None

    async def chat(
        self,
        messages: list[dict],
        model: str = "gemini-2.5-flash",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 25.0,
    ) -> ProviderResult:
        start = time.time()
        contents, system_parts = self._convert_messages(messages)

        if not contents:
            raise RuntimeError("No user/assistant messages to send to Gemini")

        body: dict = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        if system_parts:
            body["systemInstruction"] = {"parts": system_parts}

        url = f"{_GEMINI_BASE}/v1beta/models/{model}:generateContent"
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = int((time.time() - start) * 1000)

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates. Response: {data}")

        text = ""
        for part in candidates[0].get("content", {}).get("parts", []):
            if "text" in part:
                text += part["text"]

        if not text:
            raise RuntimeError("Gemini returned empty text")

        tokens = data.get("usageMetadata", {}).get("totalTokenCount")
        self.mark_success()
        return ProviderResult(
            text=text,
            model=model,
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
        """
        Generate an image using Gemini's image generation capability.
        Uses gemini-2.0-flash-exp-image-generation as the model.
        Returns a base64 data-URL.
        """
        import base64

        img_model = "gemini-2.0-flash-exp-image-generation"
        start = time.time()

        body = {
            "contents": [
                {"role": "user", "parts": [{"text": f"Generate an image: {prompt}"}]}
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
            },
        }

        url = f"{_GEMINI_BASE}/v1beta/models/{img_model}:generateContent"
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = int((time.time() - start) * 1000)

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini image generation: no candidates")

        for part in candidates[0].get("content", {}).get("parts", []):
            inline = part.get("inlineData", {})
            if inline.get("data"):
                mime = inline.get("mimeType", "image/jpeg")
                b64 = inline["data"]
                data_url = f"data:{mime};base64,{b64}"
                self.mark_success()
                return ImageResult(
                    url=data_url,
                    base64=b64,
                    model=img_model,
                    provider=self.provider_id,
                    latency_ms=latency_ms,
                )

        raise RuntimeError("Gemini image generation returned no image data")
