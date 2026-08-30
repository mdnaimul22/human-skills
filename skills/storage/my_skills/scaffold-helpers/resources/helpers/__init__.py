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
    RateLimitError,
    AuthenticationError
)
from .date_utils import time_now, time_now_iso, parse_iso, format_iso, relative_time
from .retry import retry_on_failure, retry_async_on_failure
from .port_utils import get_pid, kill_pid

__all__ = [
    # Exceptions
    "AppError",
    "NotFoundError",
    "ValidationError",
    "ExternalServiceError",
    "PermissionDeniedError",
    "ConflictError",
    "RateLimitError",
    "AuthenticationError",
    # Date Utils
    "time_now",
    "time_now_iso",
    "parse_iso",
    "format_iso",
    "relative_time",
    # Retry
    "retry_on_failure",
    "retry_async_on_failure",
    # Network
    "get_pid",
    "kill_pid",
]

# ── Optional: FastAPI Components ──────────────────────────────────────────────
try:
    from .cors import register_cors
    from .middleware import register_middleware
    from .error_handlers import register_error_handlers
    from .rate_limit import RateLimiter
    from .nginx import generate_nginx_config
    
    __all__.extend([
        "register_cors",
        "register_middleware",
        "register_error_handlers",
        "RateLimiter",
        "generate_nginx_config",
    ])
except ImportError:
    _has_fastapi = False

# ── Optional: Database Components ─────────────────────────────────────────────
try:
    from .connection import init_db, get_session, shutdown_db, session_scope
    from .repository import BaseRepository
    
    __all__.extend([
        "init_db",
        "get_session",
        "shutdown_db",
        "session_scope",
        "BaseRepository",
    ])
except ImportError:
    _has_sqlalchemy = False
