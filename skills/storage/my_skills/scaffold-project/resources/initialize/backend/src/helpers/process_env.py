import os
from typing import Optional
from src.config import Settings, is_dir

_SENSITIVE_KEYS = (
    "JWT_SECRET",
    "DATABASE_URL",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_CLIENT_ID",
)

_PROXY_ENV_KEYS = (
    "http_proxy", "HTTP_PROXY",
    "https_proxy", "HTTPS_PROXY",
    "all_proxy", "ALL_PROXY",
    "no_proxy", "NO_PROXY",
)

def get_ytdlp_process_env(
    effective_proxy: Optional[str] = None,
    bypass_cdn_proxy: bool = False,
    cdn_bypass_domains: Optional[list[str]] = None,
) -> dict[str, str]:
    env = dict(os.environ)
    for key in _SENSITIVE_KEYS:
        env.pop(key, None)

    for key in _PROXY_ENV_KEYS:
        env.pop(key, None)

    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    if effective_proxy:
        env["http_proxy"] = effective_proxy
        env["HTTP_PROXY"] = effective_proxy
        env["https_proxy"] = effective_proxy
        env["HTTPS_PROXY"] = effective_proxy
        env["all_proxy"] = effective_proxy
        env["ALL_PROXY"] = effective_proxy

    return env


def inject_gpu_library_env(env: dict[str, str]) -> dict[str, str]:
    raw_dirs = [d.strip() for d in Settings.SYSTEM_GPU_LIB_DIRS.split(",") if d.strip()]
    valid_dirs = [d for d in raw_dirs if is_dir(d)]
    if not valid_dirs:
        return env
    existing_raw = env.get("LD_LIBRARY_PATH", "")
    existing_parts = [p for p in existing_raw.split(":") if p]
    to_prepend = [d for d in valid_dirs if d not in existing_parts]
    if not to_prepend:
        return env
    env["LD_LIBRARY_PATH"] = ":".join([*to_prepend, *existing_parts])
    return env


def get_ffmpeg_process_env(proxy_url: Optional[str] = None) -> dict[str, str]:
    env = dict(os.environ)
    for key in _SENSITIVE_KEYS:
        env.pop(key, None)
    for key in _PROXY_ENV_KEYS:
        env.pop(key, None)
    if proxy_url:
        env["http_proxy"] = proxy_url
        env["HTTP_PROXY"] = proxy_url
        env["https_proxy"] = proxy_url
        env["HTTPS_PROXY"] = proxy_url
        env["all_proxy"] = proxy_url
        env["ALL_PROXY"] = proxy_url
    return inject_gpu_library_env(env)

