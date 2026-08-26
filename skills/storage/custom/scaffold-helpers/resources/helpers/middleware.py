"""
HTTP Middleware — FastAPI
==========================
Production-grade middleware stack:
    1. Request-ID generation & injection (X-Request-ID header)
    2. Request latency measurement & structured logging
    3. Security headers (OWASP recommended)
    4. HSTS in production mode

Usage in main.py:
    from src.api.middleware import register_middleware
    register_middleware(app, logger, settings)

Client-side benefit:
    Every response carries X-Request-ID — clients report this ID when filing bugs.
"""

import time
import uuid

from fastapi import Request, Response


def register_middleware(app, logger, settings) -> None:
    """
    Register HTTP middleware on the FastAPI app.

    Args:
        app:      FastAPI application instance.
        logger:   Logger from setup_logger (for structured request logging).
        settings: Settings instance (for is_production / is_development checks).
    """

    @app.middleware("http")
    async def request_lifecycle(request: Request, call_next):
        # ── 1. Generate unique Request ID ───────────────────────────────────
        request_id = uuid.uuid4().hex[:8]

        # ── 2. Measure latency ──────────────────────────────────────────────
        start = time.perf_counter()
        response: Response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000

        # ── 3. Structured request log ───────────────────────────────────────
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({latency_ms:.1f}ms)"
        )

        # ── 4. Inject Request-ID header ─────────────────────────────────────
        response.headers["X-Request-ID"] = request_id

        # ── 5. Security headers (OWASP recommended) ────────────────────────
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ── 6. HSTS in production ───────────────────────────────────────────
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # ── 7. Disable caching for static assets in development ─────────────
        if settings.is_development and request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response
