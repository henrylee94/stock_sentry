"""
Rate Limiter - Token bucket for API rate limiting
Used for Finnhub (60 calls/minute free tier) and other APIs
"""

import time
import threading
from typing import Optional


class RateLimiter:
    """
    Simple token bucket rate limiter.
    Thread-safe for use in async/sync code.
    """

    def __init__(self, max_calls: int, period_seconds: int):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.tokens = max_calls
        self.last_update = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_update
        refill = elapsed * (self.max_calls / self.period_seconds)
        self.tokens = min(self.max_calls, self.tokens + refill)
        self.last_update = now

    def acquire(self, blocks: bool = True, timeout: Optional[float] = None) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            if not blocks:
                return False
            wait_time = (1 - self.tokens) * (self.period_seconds / self.max_calls)
            if timeout is not None:
                wait_time = min(wait_time, timeout)

        if wait_time > 0:
            time.sleep(wait_time)

        with self._lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def can_call(self) -> bool:
        with self._lock:
            self._refill()
            return self.tokens >= 1

    def remaining(self) -> float:
        with self._lock:
            self._refill()
            return self.tokens

    def wait_if_needed(self):
        self.acquire(blocks=True)


FINNHUB_RATE_LIMIT = 60
FINNHUB_PERIOD = 60


def get_finnhub_limiter() -> RateLimiter:
    return RateLimiter(FINNHUB_RATE_LIMIT, FINNHUB_PERIOD)
