import os
import re
from typing import TypeVar
from src.config import get_abs_path

T = TypeVar("T")

_ROOT_DIR = get_abs_path("").rstrip("/")
_FS_ROOT_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9_:/])(?:/(?:home|tmp|var|etc|usr|opt|root|srv|bin|sbin)/[^\s\"':;<>?*]+|[A-Za-z]:\\[^\s\"':;<>?*]+)"
)
_PROXY_URL_PATTERN = re.compile(
    r"(https?|socks5|socks4)://(?:([^:@\s]+):([^@\s]+)@)?([a-zA-Z0-9.-]+)(?::(\d+))?"
)

def _clean_path_match(m: re.Match) -> str:
    raw = m.group(0).rstrip("/\\")
    base = os.path.basename(raw.replace("\\", "/"))
    return base if base else "<path>"

def sanitize_proxy_url(url: str) -> str:
    if not url:
        return url
    def repl(m: re.Match) -> str:
        proto, user, pwd, host, port = m.groups()
        auth = "***:***@" if (user or pwd) else ""
        ip_parts = host.split(".")
        if len(ip_parts) == 4 and all(p.isdigit() for p in ip_parts):
            masked_host = f"{ip_parts[0]}.{ip_parts[1]}.***.***"
        else:
            masked_host = host[:3] + "***" if len(host) > 6 else host
        port_str = f":{port}" if port else ""
        return f"{proto}://{auth}{masked_host}{port_str}"
    return _PROXY_URL_PATTERN.sub(repl, url)

def sanitize_proxy_node_name(name: str) -> str:
    if not name:
        return name
    if "://" in name:
        return sanitize_proxy_url(name)
    parts = name.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        ip_parts = parts[0].split(".")
        if len(ip_parts) == 4 and all(p.isdigit() for p in ip_parts):
            return f"{ip_parts[0]}.{ip_parts[1]}.***.***:{parts[1]}"
    return name

def _sanitize_str(text: str) -> str:
    if not text:
        return text
    cleaned = text
    if _ROOT_DIR in cleaned:
        cleaned = re.sub(re.escape(_ROOT_DIR) + r"/[^\s\"':;<>?*]*", _clean_path_match, cleaned)
        cleaned = cleaned.replace(_ROOT_DIR, "<root>")
    return _FS_ROOT_PATTERN.sub(_clean_path_match, cleaned)

def sanitize_client_path(target: T) -> T:
    match target:
        case None:
            return target
        case str() as s:
            return _sanitize_str(s)
        case dict() as d:
            return {k: sanitize_client_path(v) for k, v in d.items()}
        case list() as l:
            return [sanitize_client_path(item) for item in l]
        case tuple() as t:
            return tuple(sanitize_client_path(item) for item in t)
        case BaseException() as e:
            return _sanitize_str(str(e))
        case _:
            return target
