from __future__ import annotations

from typing import Protocol
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class CorsSettingsProtocol(Protocol):
    @property
    def is_development(self) -> bool: ...

    API_PORT: int
    FRONTEND_URL: str
    EXTRA_CORS_ORIGINS: str


def register_cors(app: FastAPI, settings: CorsSettingsProtocol) -> None:
    origins: set[str] = set()

    if settings.is_development:
        api_port = settings.API_PORT
        origins.update([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            f"http://localhost:{api_port}",
            f"http://127.0.0.1:{api_port}",
        ])

    frontend_url = settings.FRONTEND_URL
    if frontend_url:
        origins.add(frontend_url.rstrip("/"))

    extra = settings.EXTRA_CORS_ORIGINS
    if extra:
        for origin in extra.split(","):
            clean = origin.strip().rstrip("/")
            if clean:
                origins.add(clean)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(origins),
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        allow_credentials=True,
        max_age=3600,
    )
