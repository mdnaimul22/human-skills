from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    id: str = ""
    tier: str = "registered"
    scopes: frozenset[str] = frozenset()
    jti: str = ""
    email: str = ""
    name: str = ""
    avatar_url: str | None = None
    access_token: str | None = None

class TokenClaims(BaseModel):
    model_config = ConfigDict(frozen=True)

    sub: str
    tier: str = "registered"
    typ: str = "access"
    jti: str = ""
    iat: int = 0
    exp: int = 0
    scopes: tuple[str, ...] = ()

class ProviderCredential(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str
    subject: str
    access_token: str | None = None
    expires_at: datetime | None = None

class AuthSessionBundle(BaseModel):
    model_config = ConfigDict(frozen=True)

    token: str
    access_token: str
    refresh_token: str
    session_id: str
    user_id: str
    name: str
    email: str
    avatar_url: str | None = None
    tier: str = "registered"
