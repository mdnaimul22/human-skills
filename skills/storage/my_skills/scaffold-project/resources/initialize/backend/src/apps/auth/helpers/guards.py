from __future__ import annotations
from typing import Callable, Coroutine
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.auth.helpers.schema import Principal
from src.apps.auth.helpers.tokens import decode_token_claims
from src.apps.auth.helpers.vault import decrypt_secret
from src.config import set_telemetry
from src.db import (
    IdentityRepository, RevokedTokenRepository, UserRepository, get_session,
)
from src.helpers import AuthenticationError, PermissionDeniedError

def _extract_bearer(authorization: str | None) -> str | None:
    if type(authorization) is not str or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    return token if token else None

def _extract_fallback_token(request: Request | None, authorization: str | None) -> str | None:
    bearer = _extract_bearer(authorization)
    if bearer:
        return bearer
    if request is None:
        return None
    raw_token = request.query_params.get("token") or request.cookies.get("access_token")
    if not raw_token:
        return None
    cleaned = raw_token[7:].strip() if raw_token.startswith("Bearer ") else raw_token.strip()
    return cleaned if cleaned else None

async def _resolve_principal(
    token: str, request: Request | None, session: AsyncSession,
) -> Principal:
    claims = decode_token_claims(token)
    if claims.jti and await RevokedTokenRepository(session).is_revoked(claims.jti):
        raise AuthenticationError("Token has been revoked")
    user = await UserRepository(session).get(claims.sub)
    if user is None or not user.is_active:
        raise AuthenticationError("User not found")
    uid_str = str(user.id)
    identity = await IdentityRepository(session).find_for_user(uid_str, "google")
    provider_token = decrypt_secret(identity.access_token_enc) if identity is not None else None
    if request is not None:
        request.state.user_id = uid_str
    set_telemetry(user_id=uid_str)
    return Principal(
        user_id=uid_str, id=uid_str, tier=user.tier, scopes=frozenset(claims.scopes),
        jti=claims.jti, email=user.email, name=user.name,
        avatar_url=user.avatar_url, access_token=provider_token,
    )

async def require_principal(
    request: Request = None,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> Principal:
    token = _extract_bearer(authorization)
    if not token:
        raise AuthenticationError("Missing or invalid Authorization header")
    return await _resolve_principal(token, request, session)

async def optional_principal(
    request: Request = None,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> Principal | None:
    token = _extract_fallback_token(request, authorization)
    if not token:
        return None
    try:
        return await _resolve_principal(token, request, session)
    except Exception:
        return None

def require_scope(required_scope: str) -> Callable[..., Coroutine[None, None, Principal]]:
    async def _guard(principal: Principal = Depends(require_principal)) -> Principal:
        if required_scope not in principal.scopes and "*" not in principal.scopes:
            raise PermissionDeniedError(f"Missing required scope: {required_scope}")
        return principal
    return _guard

get_current_user = require_principal
get_optional_user = optional_principal
