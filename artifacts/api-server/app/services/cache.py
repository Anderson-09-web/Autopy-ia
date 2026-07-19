"""
Cache service — Redis if available, otherwise in-memory RAM cache.
"""
import hashlib
import json
import time
from typing import Any

from app.config import settings


class _MemoryCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 300):
        self._store[key] = (value, time.time() + ttl)

    def stats(self) -> dict:
        now = time.time()
        valid = sum(1 for _, (_, exp) in self._store.items() if exp > now)
        return {"type": "memory", "entries": valid}


class CacheService:
    """Unified cache interface."""

    def __init__(self):
        self._redis = None
        self._memory = _MemoryCache()
        self._hits = 0
        self._misses = 0
        self._try_redis()

    def _try_redis(self):
        if not settings.redis_url:
            return
        try:
            import redis
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    @staticmethod
    def _make_key(prefix: str, **kwargs) -> str:
        raw = json.dumps(kwargs, sort_keys=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:32]
        return f"autopy:{prefix}:{digest}"

    def get(self, key: str) -> Any | None:
        if self._redis:
            try:
                raw = self._redis.get(key)
                if raw:
                    self._hits += 1
                    return json.loads(raw)
            except Exception:
                pass
        val = self._memory.get(key)
        if val is not None:
            self._hits += 1
        else:
            self._misses += 1
        return val

    def set(self, key: str, value: Any, ttl: int = 300):
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value))
                return
            except Exception:
                pass
        self._memory.set(key, value, ttl)

    def chat_key(self, messages: list, model: str | None) -> str:
        return self._make_key("chat", messages=messages, model=model)

    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / total, 3) if total > 0 else 0.0

    def backend_type(self) -> str:
        return "redis" if self._redis else "memory"


# Global singleton
cache = CacheService()
