from __future__ import annotations
import enum
from typing import Optional
from pydantic import BaseModel, Field, TypeAdapter
from src.helpers import ValidationError


class TunnelProvider(str, enum.Enum):
    CLOUDFLARED = "cloudflared"
    TAILSCALE = "tailscale"


class TunnelState(str, enum.Enum):
    DISABLED = "disabled"
    STANDBY = "standby"
    STARTING = "starting"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    STOPPING = "stopping"
    ERROR = "error"


class TunnelEventType(str, enum.Enum):
    INFO = "info"
    DOWNLOADING = "downloading"
    DOWNLOAD_COMPLETE = "download_complete"
    STARTING = "starting"
    LOGIN_REQUIRED = "login_required"
    URL_READY = "url_ready"
    STOPPED = "stopped"
    ERROR = "error"


_PROVIDER_ALIASES: dict[str, TunnelProvider] = {
    "cloudflared": TunnelProvider.CLOUDFLARED,
    "cloudflare": TunnelProvider.CLOUDFLARED,
    "cloudflare_tunnel": TunnelProvider.CLOUDFLARED,
    "cloudflare-tunnel": TunnelProvider.CLOUDFLARED,
    "tailscale": TunnelProvider.TAILSCALE,
    "tailscale_funnel": TunnelProvider.TAILSCALE,
    "tailscale-funnel": TunnelProvider.TAILSCALE,
}


def normalize_provider(raw: str) -> TunnelProvider:
    key = raw.strip().lower()
    resolved = _PROVIDER_ALIASES.get(key)
    if resolved is None:
        supported = ", ".join(p.value for p in TunnelProvider)
        raise ValidationError(f"Unsupported tunnel provider '{raw}'. Supported: {supported}")
    return resolved


class TunnelEvent(BaseModel):
    event: TunnelEventType
    message: str
    timestamp: str
    url: Optional[str] = None
    provider: Optional[str] = None


class TunnelStatus(BaseModel):
    manager_enabled: bool
    tunnel_enabled: bool
    state: TunnelState
    provider: TunnelProvider
    target_host: str
    target_port: int = Field(ge=1, le=65535)
    public_url: Optional[str] = None
    origin: Optional[str] = None
    restart_count: int = Field(default=0, ge=0)
    last_error: Optional[str] = None
    started_at: Optional[str] = None
    updated_at: str


class TunnelPersistedState(BaseModel):
    provider: TunnelProvider
    target_host: str
    target_port: int = Field(ge=1, le=65535)
    public_url: Optional[str] = None
    state: TunnelState
    updated_at: str


TUNNEL_STATE_ADAPTER: TypeAdapter[TunnelPersistedState] = TypeAdapter(TunnelPersistedState)
