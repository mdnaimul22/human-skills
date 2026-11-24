from __future__ import annotations
from typing import Optional
from urllib.parse import urlparse

_DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443, "ws": 80, "wss": 443}


def origin_from_url(value: str) -> Optional[str]:
    clean = value.strip()
    if not clean:
        return None
    parsed = urlparse(clean)
    if not parsed.scheme or not parsed.hostname:
        return None
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    try:
        port = parsed.port
    except ValueError:
        return None
    if port and port != _DEFAULT_PORTS.get(scheme):
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


def origin_key(value: str) -> Optional[tuple[str, str, int]]:
    origin = origin_from_url(value)
    if not origin:
        return None
    parsed = urlparse(origin)
    try:
        port = parsed.port or _DEFAULT_PORTS.get(parsed.scheme)
    except ValueError:
        return None
    if not parsed.scheme or not parsed.hostname or port is None:
        return None
    return parsed.scheme, parsed.hostname.lower(), int(port)


def normalize_public_url(value: str) -> str:
    clean = value.strip().rstrip("/")
    if not clean:
        return ""
    if "://" not in clean:
        return f"https://{clean}"
    return clean
