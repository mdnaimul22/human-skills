"""
Authentication Core — JWT token creation/verification + password hashing.

Uses bcrypt directly for passwords and PyJWT for tokens.
Pure business logic — completely independent of HTTP frameworks or databases.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

import bcrypt
import jwt

from src.config import Settings
from src.helpers import ValidationError, AuthenticationError, time_now


async def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt asynchronously."""
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        raise ValidationError("Password cannot exceed 72 bytes in length")
    return await asyncio.to_thread(
        lambda: bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")
    )


async def verify_password(password: str, hashed: str) -> bool:
    """Compare plaintext against stored bcrypt hash asynchronously."""
    def _verify() -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    return await asyncio.to_thread(_verify)


def create_token(user_id: str, extra_claims: dict | None = None) -> str:
    """Create a JWT token for a given user_id with optional custom claims."""
    payload = {
        "sub": user_id,
        "exp": time_now() + timedelta(hours=Settings.JWT_EXPIRY_HOURS),
        "iat": time_now(),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, Settings.JWT_SECRET, algorithm="HS256")


def decode_token_payload(token: str) -> dict:
    """Decode JWT and return full payload dict. Raises AuthenticationError on failure."""
    try:
        payload = jwt.decode(token, Settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


def decode_token(token: str) -> str:
    """Decode JWT and return subject (user_id). Raises AuthenticationError on failure."""
    payload = decode_token_payload(token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token: missing subject")
    return user_id
