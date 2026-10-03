from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Literal

import bcrypt
import jwt

from src.config import Settings
from src.helpers import ValidationError, AuthenticationError, time_now

TokenPurpose = Literal["access", "refresh", "verify_email", "reset_password"]

_EXPIRY_MAP: dict[TokenPurpose, timedelta] = {
    "access": timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRY_MINUTES),
    "refresh": timedelta(hours=Settings.REFRESH_TOKEN_EXPIRY_HOURS),
    "verify_email": timedelta(hours=Settings.VERIFY_TOKEN_EXPIRY_HOURS),
    "reset_password": timedelta(hours=Settings.RESET_TOKEN_EXPIRY_HOURS),
}


async def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        raise ValidationError("Password cannot exceed 72 bytes in length")
    return await asyncio.to_thread(
        lambda: bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")
    )


async def verify_password(password: str, hashed: str) -> bool:
    def _verify() -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    return await asyncio.to_thread(_verify)


def create_token(user_id: str, purpose: TokenPurpose, extra_claims: dict | None = None) -> str:
    now = time_now()
    payload = {
        "sub": user_id,
        "purpose": purpose,
        "exp": now + _EXPIRY_MAP[purpose],
        "iat": now,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, Settings.JWT_SECRET, algorithm="HS256")


def decode_token_payload(token: str, expected_purpose: TokenPurpose) -> dict:
    try:
        payload = jwt.decode(token, Settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

    if payload.get("purpose") != expected_purpose:
        raise AuthenticationError(f"Invalid token purpose: expected {expected_purpose}")
    return payload


def decode_token(token: str, expected_purpose: TokenPurpose) -> str:
    payload = decode_token_payload(token, expected_purpose)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token: missing subject")
    return user_id
