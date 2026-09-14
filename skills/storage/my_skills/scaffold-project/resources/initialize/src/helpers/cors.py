"""
CORS Configuration — FastAPI
==============================
Settings-driven CORS middleware. Zero hardcoding.

Usage in main.py:
    from src.api.cors import register_cors
    register_cors(app, settings)

All origins are derived from Settings (API_HOST, API_PORT, FRONTEND_URL).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import Settings


def register_cors(app: FastAPI, settings: Settings) -> None:
    origins: list[str] = [f"http://{settings.API_HOST}:{settings.API_PORT}"]

    if settings.FRONTEND_URL:
        for u in settings.FRONTEND_URL.split(","):
            clean = u.strip()
            if clean and clean not in origins:
                origins.append(clean)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
    )
