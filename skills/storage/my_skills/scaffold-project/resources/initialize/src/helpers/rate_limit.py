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
    """Simple sliding-window rate limiter with proxy header detection and memory cleanup."""

    def __init__(self, max_calls: int = 5, window_seconds: int = 60) -> None:
        self._max = max_calls
        self._window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.monotonic()

    def _extract_ip(self, request: Request) -> str:
        """Extract client IP, checking trusted reverse proxy headers first."""
        # Cloudflare header
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip.strip()

        # Standard X-Forwarded-For header (client, proxy1, proxy2)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Standard X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        return request.client.host if request.client else "unknown"

    def _cleanup_stale_entries(self, now: float) -> None:
        """Prune inactive IP addresses to prevent memory leaks."""
        cutoff = now - self._window
        stale_ips = [ip for ip, timestamps in self._hits.items() if not timestamps or timestamps[-1] <= cutoff]
        for ip in stale_ips:
            del self._hits[ip]
        self._last_cleanup = now

    def check(self, request: Request) -> None:
        """Raise RateLimitError if IP has exceeded the limit."""
        ip = self._extract_ip(request)
        now = time.monotonic()
        cutoff = now - self._window

        # Periodic cleanup every 5 minutes or if dict grows large
        if now - self._last_cleanup > 300 or len(self._hits) > 1000:
            self._cleanup_stale_entries(now)

        # Prune expired timestamps for current IP
        hits = self._hits[ip]
        self._hits[ip] = [t for t in hits if t > cutoff]

        if len(self._hits[ip]) >= self._max:
            raise RateLimitError(
                f"Too many requests (max {self._max} per {self._window}s)",
                retry_after=self._window,
            )

        self._hits[ip].append(now)
