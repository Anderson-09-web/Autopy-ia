"""
Groq provider — ultra-fast inference via Groq API.
Tracks rate limits per-model so a 429 on one model automatically
retries the next available Groq model instead of blocking the whole provider.
"""
import time

from app.services.providers.base import BaseProvider, ProviderResult

# Models tried in order (fastest / most available first)
_GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "llama-3.3-70b-versatile",
]

# How long to back off a rate-limited model (seconds)
_MODEL_BACKOFF_SECS = 60


class GroqProvider(BaseProvider):
    name = "Groq"
    provider_id = "groq"
    priority = 1

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self._client = None
        # Per-model backoff: model_id → epoch time when it becomes available again
        self._model_backoff: dict[str, float] = {}

    def _get_client(self):
        if self._client is None:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    def _available_models(self, preferred: str | None) -> list[str]:
        """Return models to try, preferred first, skipping rate-limited ones."""
        now = time.time()
        available = [m for m in _GROQ_MODELS if self._model_backoff.get(m, 0) <= now]

        # If caller requested a specific model, put it first
        if preferred:
            if preferred in available:
                available.remove(preferred)
                available.insert(0, preferred)
            elif preferred not in _GROQ_MODELS and self._model_backoff.get(preferred, 0) <= now:
                # Unknown model (e.g. passed directly by user), try it first
                available.insert(0, preferred)

        return available

    async def chat(
        self,
        messages: list[dict],
        model: str = "llama-3.1-8b-instant",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 30.0,
    ) -> ProviderResult:
        client = self._get_client()
        models_to_try = self._available_models(model)

        if not models_to_try:
            # Every model is in backoff — tell the orchestrator this provider is busy
            self.mark_rate_limited()
            raise RuntimeError("All Groq models are rate-limited; try again shortly")

        last_error: Exception | None = None
        for m in models_to_try:
            start = time.time()
            try:
                response = await client.chat.completions.create(
                    model=m,
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
            except Exception as e:
                err = str(e).lower()
                if "rate_limit" in err or "rate limit" in err or "429" in err:
                    # Back off just this model, keep trying others
                    self._model_backoff[m] = time.time() + _MODEL_BACKOFF_SECS
                    last_error = e
                    continue
                else:
                    self.mark_failed()
                    raise

        # All models are rate-limited
        self.mark_rate_limited()
        raise last_error or RuntimeError("All Groq models failed")
