"""
CORS Configuration — FastAPI
==============================
Settings-driven CORS middleware. Zero hardcoding.

Usage in main.py:
    from src.api.cors import register_cors
    register_cors(app, settings)

All origins are derived from Settings (API_HOST, API_PORT, FRONTEND_URL).
"""

from fastapi.middleware.cors import CORSMiddleware


def register_cors(app, settings) -> None:
    """
    Register CORS middleware driven entirely by Settings.

    Automatically includes:
        - http://{API_HOST}:{API_PORT}  (self-origin for dev)
        - Settings.FRONTEND_URL         (if configured)

    Args:
        app:      FastAPI application instance.
        settings: Settings instance (needs API_HOST, API_PORT, FRONTEND_URL).
    """
    origins: list[str] = []

    # Self-origin (always allowed for local dev / same-server deploy)
    if hasattr(settings, "API_HOST") and hasattr(settings, "API_PORT"):
        origins.append(f"http://{settings.API_HOST}:{settings.API_PORT}")

    # Frontend origin (SPA on a different port or domain)
    if hasattr(settings, "FRONTEND_URL") and settings.FRONTEND_URL:
        origins.append(settings.FRONTEND_URL)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
    )
