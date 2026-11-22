from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

class NginxState(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    backend_domain: str = Field(..., min_length=1)
    frontend_domain: str = Field(..., min_length=1)
    config_hash: str = Field(..., min_length=1)
    deployed_files: list[str] = Field(default_factory=list)
    last_reloaded_at: Optional[str] = None

class NginxStatus(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    installed: bool = False
    running: bool = False
    backend_domain: str = ""
    frontend_domain: str = ""
    ssl_enabled: bool = False
    modsec_enabled: bool = False
    config_hash: str = ""

class VHostSpec(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    backend_domain: str = Field(..., min_length=1)
    frontend_domain: str = Field(..., min_length=1)
    api_port: int = Field(default=8000, ge=1, le=65535)
    rate_limit_zone_size: str = Field(default="10m", min_length=1)
    rate_limit_rate: str = Field(default="30r/s", min_length=1)
    rate_limit_burst: int = Field(default=50, ge=0)
    google_verification_code: Optional[str] = None
    modsec_enabled: bool = False
    backend_ssl: bool = False
    frontend_ssl: bool = False

NGINX_STATE_ADAPTER: TypeAdapter[NginxState] = TypeAdapter(NginxState)
NGINX_STATUS_ADAPTER: TypeAdapter[NginxStatus] = TypeAdapter(NginxStatus)
VHOST_SPEC_ADAPTER: TypeAdapter[VHostSpec] = TypeAdapter(VHostSpec)
