import asyncio
import os
import time
from collections import deque
from contextlib import asynccontextmanager
import random

_MAX_CALLS = int(os.getenv("RATE_LIMIT_MAX_CALLS", "4"))          # tune as needed
_PERIOD = float(os.getenv("RATE_LIMIT_PERIOD", "1.0"))            # seconds
_MAX_RETRIES = int(os.getenv("RATE_LIMIT_MAX_RETRIES", "4"))
_BASE_BACKOFF = float(os.getenv("RATE_LIMIT_BASE_BACKOFF", "1.0")) # seconds
_MAX_BACKOFF = float(os.getenv("RATE_LIMIT_MAX_BACKOFF", "12.0"))

class AsyncRateLimiter:
    """
    Simple sliding window limiter:
    - Maintains timestamps of recent calls
    - Waits if adding a new call would exceed max_calls in period
    """
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self._events = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            # purge old
            while self._events and now - self._events[0] >= self.period:
                self._events.popleft()
            if len(self._events) >= self.max_calls:
                sleep_for = self.period - (now - self._events[0]) + 0.01
                await asyncio.sleep(sleep_for)
                return await self.acquire()
            self._events.append(time.monotonic())

GLOBAL_RATE_LIMITER = AsyncRateLimiter(_MAX_CALLS, _PERIOD)

def compute_backoff(attempt: int) -> float:
    """Exponential backoff with jitter."""
    raw = min(_BASE_BACKOFF * (2 ** attempt), _MAX_BACKOFF)
    return raw * (0.7 + random.random() * 0.6)  # jitter ~70%-130%

@asynccontextmanager
async def rate_limited():
    await GLOBAL_RATE_LIMITER.acquire()
    yield

__all__ = [
    "GLOBAL_RATE_LIMITER",
    "rate_limited",
    "compute_backoff",
    "_MAX_RETRIES"
]
