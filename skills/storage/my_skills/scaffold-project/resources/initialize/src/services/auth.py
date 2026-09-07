"""
Service — Authentication.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, setup_logger
from src.core.auth import hash_password, verify_password, create_token
from src.helpers import ConflictError, AuthenticationError, PermissionDeniedError
from src.db import UserRepository
from src.schema.auth import TokenResponse
from src.providers import send_welcome_email

logger = setup_logger(Settings.LOG_DIR / "service.log", name="app.services.auth")


async def register(email: str, name: str, password: str, session: AsyncSession) -> TokenResponse:
    """Register a new user. Returns token + user info."""
    repo = UserRepository(session)

    existing = await repo.find_by_email(email)
    if existing:
        raise ConflictError(f"Email already registered: {email}")

    hashed = await hash_password(password)
    user = await repo.create_user(email, name, hashed)
    await session.commit()
    await session.refresh(user)

    token = create_token(user.id)
    logger.info(f"User registered: {user.email} (id={user.id})")

    # Orchestrate external provider: dispatch welcome notification safely
    try:
        await send_welcome_email(user.email, user.name)
    except Exception as e:
        logger.warning(f"Failed to send welcome email to {user.email}: {e}")

    return TokenResponse(
        token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
    )


async def login(email: str, password: str, session: AsyncSession) -> TokenResponse:
    """Authenticate user and return JWT token."""
    repo = UserRepository(session)
    user = await repo.find_by_email(email)

    if not user or not await verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    if hasattr(user, "is_active") and not user.is_active:
        raise PermissionDeniedError("Account is inactive")

    token = create_token(user.id)
    logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
    )
