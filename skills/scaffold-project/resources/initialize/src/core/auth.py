"""
Authentication — JWT token creation/verification + password hashing.

Uses bcrypt directly for passwords and PyJWT for tokens.
No business logic — pure utility functions + FastAPI dependency.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.helpers import ValidationError, PermissionDeniedError, time_now
from src.db import get_session, UserRepository, User


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Compare plaintext against stored bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str) -> str:
    """Create a JWT token for a given user_id."""
    payload = {
        "sub": user_id,
        "exp": time_now() + timedelta(hours=Settings.JWT_EXPIRY_HOURS),
        "iat": time_now(),
    }
    return jwt.encode(payload, Settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> str:
    """Decode JWT and return user_id. Raises on invalid/expired."""
    try:
        payload = jwt.decode(token, Settings.JWT_SECRET, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise ValidationError("Invalid token: missing subject")
        return user_id
    except jwt.ExpiredSignatureError:
        raise PermissionDeniedError("Token expired")
    except jwt.InvalidTokenError:
        raise PermissionDeniedError("Invalid token")


async def get_current_user(
    authorization: str = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    FastAPI dependency — extracts user from Authorization header.
    Usage: user: User = Depends(get_current_user)
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
    FastAPI dependency — returns User if token provided, None otherwise.
    For endpoints that work both anonymously and authenticated.
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
