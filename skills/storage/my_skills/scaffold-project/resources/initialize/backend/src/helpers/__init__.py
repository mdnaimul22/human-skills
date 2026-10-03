from __future__ import annotations

from .exceptions import (
    AppError,
    NotFoundError,
    ValidationError,
    ExternalServiceError,
    PermissionDeniedError,
    ConflictError,
    RateLimitError,
    AuthenticationError,
)
from .date_utils import time_now, time_now_iso, parse_iso, format_iso, relative_time
from .port_utils import get_pid, kill_pid, is_port_free
from .tailscale import (
    is_tailscale_installed,
    setup_tailscale_ingress,
    reset_tailscale_serve,
    get_tailscale_status,
    get_tailscale_guidance,
)
from .retry import retry_on_failure, retry_async_on_failure, run_with_retry
from .cors import register_cors
from .middleware import register_middleware
from .error_handlers import register_error_handlers
from .rate_limit import RateLimiter
from .nginx import generate_nginx_config
try:
    from src.config import exists
    if not exists("web"):
        raise ImportError("Frontend 'web' directory not found")
    from .frontend_runner import start_frontend, stop_frontend, get_frontend_port
    _has_frontend = True
except ImportError:
    _has_frontend = False

__all__ = [
    "AppError",
    "NotFoundError",
    "ValidationError",
    "ExternalServiceError",
    "PermissionDeniedError",
    "ConflictError",
    "RateLimitError",
    "AuthenticationError",
    "time_now",
    "time_now_iso",
    "parse_iso",
    "format_iso",
    "relative_time",
    "get_pid",
    "kill_pid",
    "is_port_free",
    "is_tailscale_installed",
    "setup_tailscale_ingress",
    "reset_tailscale_serve",
    "get_tailscale_status",
    "get_tailscale_guidance",
    "retry_on_failure",
    "retry_async_on_failure",
    "run_with_retry",
    "register_cors",
    "register_middleware",
    "register_error_handlers",
    "RateLimiter",
    "generate_nginx_config",
]

if _has_frontend:
    __all__.extend(["start_frontend", "stop_frontend", "get_frontend_port"])
