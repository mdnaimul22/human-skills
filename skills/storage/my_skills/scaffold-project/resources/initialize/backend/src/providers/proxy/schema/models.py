from __future__ import annotations
import enum
from typing import Optional
from pydantic import BaseModel, Field, TypeAdapter
from src.helpers import ValidationError


class ProxyProviderType(str, enum.Enum):
    WEBSHARE = "webshare"
    STATIC = "static"


class ProxyState(str, enum.Enum):
    DISABLED = "disabled"
    STANDBY = "standby"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ERROR = "error"


_PROVIDER_ALIASES: dict[str, ProxyProviderType] = {
    "webshare": ProxyProviderType.WEBSHARE,
    "static": ProxyProviderType.STATIC,
    "list": ProxyProviderType.STATIC,
}


def normalize_proxy_provider(raw: str) -> ProxyProviderType:
    resolved = _PROVIDER_ALIASES.get(raw.strip().lower())
    if resolved is None:
        supported = ", ".join(p.value for p in ProxyProviderType)
        raise ValidationError(f"Unsupported proxy provider '{raw}'. Supported: {supported}")
    return resolved


class ProxyCacheFile(BaseModel):
    proxies: list[str] = Field(default_factory=list)
    count: int = Field(default=0, ge=0)
    provider: ProxyProviderType = ProxyProviderType.WEBSHARE
    updated_at: Optional[str] = None


class ProxyPersistedState(BaseModel):
    state: ProxyState = ProxyState.DISABLED
    provider: ProxyProviderType = ProxyProviderType.WEBSHARE
    last_refresh_at: Optional[str] = None
    total_proxies: int = Field(default=0, ge=0)
    last_error: Optional[str] = None
    updated_at: str


class ProxyStatus(BaseModel):
    manager_enabled: bool
    proxy_enabled: bool
    state: ProxyState
    provider: ProxyProviderType
    total_proxies: int = Field(default=0, ge=0)
    healthy_proxies: int = Field(default=0, ge=0)
    cooldown_proxies: int = Field(default=0, ge=0)
    last_refresh_at: Optional[str] = None
    last_error: Optional[str] = None
    updated_at: str


PROXY_CACHE_ADAPTER: TypeAdapter[ProxyCacheFile] = TypeAdapter(ProxyCacheFile)
PROXY_STATE_ADAPTER: TypeAdapter[ProxyPersistedState] = TypeAdapter(ProxyPersistedState)
