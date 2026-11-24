from __future__ import annotations
import importlib
from typing import TypeVar

T = TypeVar("T")

_LAZY_EXPORTS: dict[str, str] = {
    "AppError": ".exceptions",
    "NotFoundError": ".exceptions",
    "ValidationError": ".exceptions",
    "ExternalServiceError": ".exceptions",
    "PermissionDeniedError": ".exceptions",
    "AuthenticationError": ".exceptions",
    "ConflictError": ".exceptions",
    "RateLimitError": ".exceptions",
    "MediaFormatError": ".exceptions",
    "MediaProcessingError": ".exceptions",
    "ErrorClassification": ".exceptions",
    "mask_sensitive_data": ".exceptions",
    "sanitize_client_error": ".exceptions",
    "sanitize_client_path": ".sanitizers",
    "sanitize_proxy_url": ".sanitizers",
    "sanitize_proxy_node_name": ".sanitizers",
    "get_now_iso": ".date_utils",
    "get_now_utc": ".date_utils",
    "parse_iso": ".date_utils",
    "format_iso": ".date_utils",
    "relative_time": ".date_utils",
    "retry_on_failure": ".retry",
    "retry_async_on_failure": ".retry",
    "get_pid": ".port_utils",
    "kill_pid": ".port_utils",
    "AsyncFileLock": ".file_lock",
    "SyncFileLock": ".file_lock",
    "try_clean_stale_lock": ".file_lock",
    "try_clean_and_remove_stale_lock": ".file_lock",
    "get_ytdlp_process_env": ".process_env",
    "get_ffmpeg_process_env": ".process_env",
    "inject_gpu_library_env": ".process_env",
    "RedisManager": ".redis_client",
    "get_redis": ".redis_client",
    "init_redis": ".redis_client",
    "shutdown_redis": ".redis_client",
    "RateLimiter": ".rate_limit",
    "register_cors": ".cors",
    "get_allowed_redirect_hosts": ".cors",
    "register_middleware": ".middleware",
    "register_error_handlers": ".error_handlers",
    "NLE_COMPAT": ".media_compat",
    "get_nle_support": ".media_compat",
    "resolve_ttl": ".file_expiry",
    "resolve_file_expiry": ".file_expiry",
}

__all__ = list(_LAZY_EXPORTS.keys())

def __getattr__(name: str) -> T:
    mod_path = _LAZY_EXPORTS.get(name)
    if mod_path is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    module = importlib.import_module(mod_path, __name__)
    val: T = module.__dict__[name]
    globals()[name] = val
    return val
