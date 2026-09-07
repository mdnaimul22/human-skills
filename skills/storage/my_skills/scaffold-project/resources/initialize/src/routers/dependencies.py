"""
FastAPI HTTP Dependencies.
Extracts authenticated user context from HTTP Authorization headers.
"""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import decode_token
from src.db import get_session, UserRepository, User
from src.helpers import PermissionDeniedError


async def get_current_user(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    FastAPI dependency — extracts authenticated user from Authorization header.
    Raises PermissionDeniedError (403) if missing, invalid, or expired.

    Usage:
        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
            ...
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise PermissionDeniedError("Missing or invalid Authorization header")

    token = authorization[7:]  # strip "Bearer "
    user_id = decode_token(token)

    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        raise PermissionDeniedError("User not found")
    return user


async def get_optional_user(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """
    FastAPI dependency — returns User if valid Bearer token provided, None otherwise.
    For endpoints that work both anonymously and with authentication.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization[7:]
        user_id = decode_token(token)
        repo = UserRepository(session)
        return await repo.get(user_id)
    except Exception:
        return None
