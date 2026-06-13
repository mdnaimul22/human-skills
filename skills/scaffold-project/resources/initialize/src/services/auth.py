"""
Service — Authentication.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, setup_logger
from src.core.auth import hash_password, verify_password, create_token
from src.helpers import ConflictError, AuthenticationError
from src.db import UserRepository

logger = setup_logger(Settings.LOG_DIR / "service.log", name="app.services.auth")


async def register(email: str, name: str, password: str, session: AsyncSession) -> dict:
    """Register a new user. Returns token + user info."""
    repo = UserRepository(session)

    existing = await repo.find_by_email(email)
    if existing:
        raise ConflictError(f"Email already registered: {email}")

    hashed = hash_password(password)
    user = await repo.create_user(email, name, hashed)

    token = create_token(user.id)
    logger.info(f"User registered: {user.email} (id={user.id})")
    return {
        "token": token,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
    }


async def login(email: str, password: str, session: AsyncSession) -> dict:
    """Authenticate user and return JWT token."""
    repo = UserRepository(session)
    user = await repo.find_by_email(email)

    if not user or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    token = create_token(user.id)
    logger.info(f"User logged in: {user.email}")
    return {
        "token": token,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
    }
