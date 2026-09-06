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
from .port_utils import get_pid, kill_pid, is_port_free

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
    # Network / Port Utils
    "get_pid",
    "kill_pid",
    "is_port_free",
]

# ── Optional: Retry Logic (requires tenacity) ─────────────────────────────────
try:
    from .retry import retry_on_failure, retry_async_on_failure, run_with_retry
    __all__.extend([
        "retry_on_failure",
        "retry_async_on_failure",
        "run_with_retry",
    ])
except ImportError:
    _has_retry = False

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

# ── Optional: Frontend Orchestration ─────────────────────────────────────────
try:
    from .frontend_runner import start_frontend, stop_frontend, get_frontend_port
    __all__.extend([
        "start_frontend",
        "stop_frontend",
        "get_frontend_port",
    ])
except ImportError:
    _has_frontend = False
