"""
In-memory per-IP rate limiter for FastAPI endpoints.

Usage:
    from src.helpers.rate_limit import RateLimiter

    _login_limiter = RateLimiter(max_calls=5, window_seconds=60)

    @router.post("/login")
    async def login(request: Request):
        _login_limiter.check(request)
        ...
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request

from src.helpers.exceptions import RateLimitError


class RateLimiter:
    """Simple sliding-window rate limiter. Thread-safe for single-process asyncio."""

    def __init__(self, max_calls: int = 5, window_seconds: int = 60) -> None:
        self._max = max_calls
        self._window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, request: Request) -> None:
        """Raise RateLimitError if IP has exceeded the limit."""
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        cutoff = now - self._window

        # Prune expired timestamps
        hits = self._hits[ip]
        self._hits[ip] = [t for t in hits if t > cutoff]

        if len(self._hits[ip]) >= self._max:
            raise RateLimitError(
                f"Too many requests (max {self._max} per {self._window}s)",
                retry_after=self._window,
            )

        self._hits[ip].append(now)
