"""
Global Error Handlers — FastAPI
================================
Maps exceptions to consistent JSON error responses.
Automatically integrates with AppError hierarchy from sethelpers (if installed).

Usage in main.py:
    from src.api.error_handlers import register_error_handlers
    register_error_handlers(app, logger)

Response format (all errors):
    {"error": "Human-readable message", "status_code": 400}
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def register_error_handlers(app, logger) -> None:
    """
    Register global exception handlers on the FastAPI app.

    Handlers (in priority order):
        1. RequestValidationError → 422 (Pydantic / query-param failures)
        2. AppError subclasses    → dynamic status_code (if sethelpers installed)
        3. Exception              → 500 catch-all (never leaks internals)
    """

    # ── 1. Pydantic / FastAPI validation errors ─────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        logger.error(f"Validation Error on {request.url.path}: {errors}")
        return JSONResponse(
            status_code=422,
            content={"error": "Validation failed", "detail": errors, "status_code": 422},
        )

    # ── 2. AppError hierarchy (from sethelpers/exceptions.py) ───────────────
    # If src/helpers/exceptions.py exists, auto-map AppError → status_code.
    # If not installed, this block is silently skipped.
    try:
        from src.helpers.exceptions import AppError

        @app.exception_handler(AppError)
        async def app_error_handler(request: Request, exc: AppError):
            logger.error(f"{exc.__class__.__name__} on {request.url.path}: {exc.message}")
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.message, "status_code": exc.status_code},
            )
    except ImportError:
        pass  # Intentional: AppError hierarchy is optional — works without src/helpers/exceptions

    # ── 3. Catch-all — prevents stack trace leaks ───────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "status_code": 500},
        )
