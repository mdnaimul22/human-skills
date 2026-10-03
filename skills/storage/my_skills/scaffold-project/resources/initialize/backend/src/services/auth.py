from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, setup_logger
from src.core.auth import hash_password, verify_password, create_token, decode_token
from src.helpers import (
    ConflictError, AuthenticationError, PermissionDeniedError,
    NotFoundError, ValidationError,
)
from src.db import UserRepository
from src.schema import AuthTokenResponse, RegisterResponse, UserProfileResponse, GoogleUserInfo
from src.providers import send_verification_email, send_password_reset_email

logger = setup_logger(boss_name="services.main.txt", his_name="services.auth.txt")


def _build_token_response(user) -> AuthTokenResponse:
    return AuthTokenResponse(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
        user_id=user.id,
        name=user.name,
        email=user.email,
    )


async def register(email: str, name: str, password: str, session: AsyncSession) -> RegisterResponse:
    repo = UserRepository(session)

    existing = await repo.find_by_email(email)
    if existing:
        raise ConflictError(f"Email already registered: {email}")

    hashed = await hash_password(password)
    user = await repo.create_user(email, name, hashed)
    await session.commit()
    await session.refresh(user)

    logger.info(f"User registered: {user.email} (id={user.id})")

    verification_token = create_token(user.id, "verify_email")
    try:
        await send_verification_email(user.email, user.name, verification_token)
    except Exception as e:
        logger.warning(f"Failed to send verification email to {user.email}: {e}")

    return RegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
        email=user.email,
    )


async def verify_email(token: str, session: AsyncSession) -> AuthTokenResponse:
    user_id = decode_token(token, "verify_email")
    repo = UserRepository(session)
    user = await repo.get(user_id)

    if not user:
        raise NotFoundError("User", user_id)
    if user.email_verified:
        raise ValidationError("Email already verified")

    await repo.set_email_verified(user_id)
    await session.commit()
    await session.refresh(user)

    logger.info(f"Email verified: {user.email}")
    return _build_token_response(user)


async def login(email: str, password: str, session: AsyncSession) -> AuthTokenResponse:
    repo = UserRepository(session)
    user = await repo.find_by_email(email)

    if not user or not user.password_hash or not await verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise PermissionDeniedError("Account is inactive")
    if not user.email_verified:
        raise AuthenticationError("Email not verified. Please check your inbox.")

    logger.info(f"User logged in: {user.email}")
    return _build_token_response(user)


async def google_login(id_token: str, session: AsyncSession) -> AuthTokenResponse:
    from src.providers.google import verify_google_token

    google_user: GoogleUserInfo = await verify_google_token(id_token)
    repo = UserRepository(session)

    user = await repo.find_by_google_id(google_user.google_id)
    if user:
        if not user.is_active:
            raise PermissionDeniedError("Account is inactive")
        logger.info(f"Google login: {user.email}")
        return _build_token_response(user)

    existing_email_user = await repo.find_by_email(google_user.email)
    if existing_email_user:
        raise ConflictError(
            f"Email {google_user.email} is already registered with local auth. "
            f"Please login with your password."
        )

    user = await repo.create_google_user(
        email=google_user.email,
        name=google_user.name,
        google_id=google_user.google_id,
    )
    await session.commit()
    await session.refresh(user)

    logger.info(f"Google user created: {user.email} (id={user.id})")
    return _build_token_response(user)


async def refresh_tokens(refresh_token: str, session: AsyncSession) -> AuthTokenResponse:
    user_id = decode_token(refresh_token, "refresh")
    repo = UserRepository(session)
    user = await repo.get(user_id)

    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise PermissionDeniedError("Account is inactive")

    return _build_token_response(user)


async def request_password_reset(email: str, session: AsyncSession) -> None:
    repo = UserRepository(session)
    user = await repo.find_by_email(email)

    if not user or user.auth_method != "local":
        return

    reset_token = create_token(user.id, "reset_password")
    try:
        await send_password_reset_email(user.email, user.name, reset_token)
        logger.info(f"Password reset email sent to: {user.email}")
    except Exception as e:
        logger.error(f"Failed to send reset email to {user.email}: {e}")


async def reset_password(token: str, new_password: str, session: AsyncSession) -> None:
    user_id = decode_token(token, "reset_password")
    repo = UserRepository(session)
    user = await repo.get(user_id)

    if not user:
        raise NotFoundError("User", user_id)
    if user.auth_method != "local":
        raise ValidationError("Cannot reset password for OAuth accounts")

    hashed = await hash_password(new_password)
    await repo.update_password(user_id, hashed)
    await session.commit()
    logger.info(f"Password reset completed: {user.email}")


async def change_password(
    user_id: str, current_password: str, new_password: str, session: AsyncSession,
) -> None:
    repo = UserRepository(session)
    user = await repo.get(user_id)

    if not user:
        raise NotFoundError("User", user_id)
    if user.auth_method != "local":
        raise ValidationError("Cannot change password for OAuth accounts")
    if not user.password_hash or not await verify_password(current_password, user.password_hash):
        raise AuthenticationError("Current password is incorrect")

    hashed = await hash_password(new_password)
    await repo.update_password(user_id, hashed)
    await session.commit()
    logger.info(f"Password changed: {user.email}")


async def update_profile(user_id: str, name: str, session: AsyncSession) -> UserProfileResponse:
    repo = UserRepository(session)
    user = await repo.update_profile(user_id, name)

    if not user:
        raise NotFoundError("User", user_id)

    await session.commit()
    await session.refresh(user)

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
        auth_method=user.auth_method,
        created_at=user.created_at,
    )
