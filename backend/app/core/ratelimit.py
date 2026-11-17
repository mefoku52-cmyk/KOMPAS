from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Protocol

from app.core.config.settings import settings


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class RateLimiter(Protocol):
    def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult: ...

    def reset(self, key: str | None = None) -> None: ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now))
                return RateLimitResult(False, 0, retry_after)
            events.append(now)
            return RateLimitResult(True, max(0, limit - len(events)), 0)

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._events.clear()
            else:
                self._events.pop(key, None)


_limiter: RateLimiter = InMemoryRateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _limiter


def set_rate_limiter(limiter: RateLimiter) -> None:
    global _limiter
    _limiter = limiter


def reset_rate_limiter() -> None:
    _limiter.reset()


def check_login_rate_limit(username: str, client_host: str | None) -> RateLimitResult:
    limiter = get_rate_limiter()
    key = f"login:{username}:{client_host or 'unknown'}"
    result = limiter.check(
        key,
        limit=settings.rate_limit_login_attempts,
        window_seconds=settings.rate_limit_login_window_seconds,
    )
    if not result.allowed:
        limiter.check(
            f"login-blocked:{client_host or 'unknown'}",
            limit=settings.rate_limit_default_per_minute,
            window_seconds=60,
        )
    return result
