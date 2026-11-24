from __future__ import annotations
import time
from collections import defaultdict
from fastapi import Request
from src.helpers.exceptions import RateLimitError

class RateLimiter:
    def __init__(self, max_calls: int = 5, window_seconds: int = 60) -> None:
        self._max = max_calls
        self._window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _resolve_ip(self, request: Request) -> str:
        ip = request.state._state.get("client_ip")
        if ip:
            return str(ip)
        raw_ip = (
            request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Real-IP")
            or request.headers.get("X-Forwarded-For")
        )
        if raw_ip:
            return raw_ip.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request, key: str | None = None) -> None:
        client_key = key or self._resolve_ip(request)
        now = time.monotonic()
        cutoff = now - self._window
        hits = self._hits[client_key]
        self._hits[client_key] = [t for t in hits if t > cutoff]
        if len(self._hits[client_key]) >= self._max:
            raise RateLimitError(
                f"Too many requests (max {self._max} per {self._window}s)",
                retry_after=self._window,
            )
        self._hits[client_key].append(now)
