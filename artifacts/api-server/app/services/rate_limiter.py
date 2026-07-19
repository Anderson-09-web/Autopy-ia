"""
In-memory sliding window rate limiter.
Keyed by API key ID. Window = 60 seconds (per minute).
"""
import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
    def __init__(self, window_seconds: int = 60):
        self._window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str, limit: int) -> tuple[bool, int]:
        """
        Check if the key is within the rate limit.
        Returns (allowed, remaining).
        limit=0 means unlimited.
        """
        if limit == 0:
            return True, 999999

        now = time.time()
        cutoff = now - self._window

        with self._lock:
            bucket = self._buckets[key]
            # Remove expired entries
            bucket[:] = [t for t in bucket if t > cutoff]
            count = len(bucket)

            if count >= limit:
                return False, 0

            bucket.append(now)
            return True, limit - count - 1


# Global singleton
rate_limiter = RateLimiter()
