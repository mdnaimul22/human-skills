"""
Global utilities and stateless helpers used across the entire project.
Single point of export for exceptions, date utilities, retry logic, 
FastAPI middleware, and Database connection layer.
"""

from .exceptions import (
    AppError,
    NotFoundError,
    ValidationError,
    ExternalServiceError,
    PermissionDeniedError,
    ConflictError,
    RateLimitError
)
from .date_utils import get_now_iso, parse_iso, format_iso, relative_time
from .retry import retry_on_failure, retry_async_on_failure

__all__ = [
    # Exceptions
    "AppError",
    "NotFoundError",
    "ValidationError",
    "ExternalServiceError",
    "PermissionDeniedError",
    "ConflictError",
    "RateLimitError",
    # Date Utils
    "get_now_iso",
    "parse_iso",
    "format_iso",
    "relative_time",
    # Retry
    "retry_on_failure",
    "retry_async_on_failure",
]

# ── Optional: FastAPI Components ──────────────────────────────────────────────
try:
    from .cors import register_cors
    from .middleware import register_middleware
    from .error_handlers import register_error_handlers
    
    __all__.extend([
        "register_cors",
        "register_middleware",
        "register_error_handlers",
    ])
except ImportError:
    pass

# ── Optional: Database Components ─────────────────────────────────────────────
try:
    from .connection import init_db, get_session, shutdown_db
    from .repository import BaseRepository
    
    __all__.extend([
        "init_db",
        "get_session",
        "shutdown_db",
        "BaseRepository",
    ])
except ImportError:
    pass
