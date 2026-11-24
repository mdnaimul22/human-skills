from __future__ import annotations
import urllib.parse
from typing import Protocol
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class CorsSettingsProtocol(Protocol):
    @property
    def is_development(self) -> bool: ...

    API_PORT: int
    FRONTEND_URL: str
    EXTRA_CORS_ORIGINS: str


class RedirectHostSettingsProtocol(CorsSettingsProtocol, Protocol):
    @property
    def is_testing(self) -> bool: ...

    ALLOWED_REDIRECT_HOSTS: str


def _extract_hosts_from_url(target: set[str], url_str: str) -> None:
    if not url_str:
        return
    parsed = urllib.parse.urlparse(url_str)
    if not parsed.hostname:
        return
    host = parsed.hostname.lower()
    target.add(host)
    if parsed.port:
        target.add(f"{host}:{parsed.port}")
    elif parsed.scheme == "https":
        target.add(f"{host}:443")
    elif parsed.scheme == "http":
        target.add(f"{host}:80")


def get_allowed_redirect_hosts(settings: RedirectHostSettingsProtocol) -> set[str]:
    hosts: set[str] = set()
    _extract_hosts_from_url(hosts, settings.FRONTEND_URL)
    cors_items = settings.EXTRA_CORS_ORIGINS.split(",") if settings.EXTRA_CORS_ORIGINS else []
    for raw_origin in cors_items:
        _extract_hosts_from_url(hosts, raw_origin.strip())
    redirect_items = settings.ALLOWED_REDIRECT_HOSTS.split(",") if settings.ALLOWED_REDIRECT_HOSTS else []
    for raw_host in redirect_items:
        val = raw_host.strip().lower()
        if val:
            hosts.add(val)
    if settings.is_development or settings.is_testing:
        hosts.update({
            "localhost", "127.0.0.1",
            "localhost:3000", f"localhost:{settings.API_PORT}",
            "127.0.0.1:3000", f"127.0.0.1:{settings.API_PORT}",
        })
    return hosts


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
