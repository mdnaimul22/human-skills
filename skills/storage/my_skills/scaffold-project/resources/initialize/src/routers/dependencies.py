from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import decode_token
from src.db import get_session, UserRepository, User
from src.helpers import AuthenticationError, PermissionDeniedError


async def get_current_user(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = authorization[7:]
    user_id = decode_token(token, "access")

    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise PermissionDeniedError("Account is inactive")
    return user


async def get_optional_user(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization[7:]
        user_id = decode_token(token, "access")
        repo = UserRepository(session)
        return await repo.get(user_id)
    except Exception:
        return None
