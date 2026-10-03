from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.schema import (
    RegisterRequest, LoginRequest, GoogleLoginRequest,
    RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest,
    ChangePasswordRequest, UpdateProfileRequest,
    AuthTokenResponse, RegisterResponse, UserProfileResponse,
    StatusResponse,
)
from src.routers.dependencies import get_current_user
from src.db import get_session, User
from src.services import auth as auth_service
from src.helpers.rate_limit import RateLimiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

_register_limiter = RateLimiter(max_calls=3, window_seconds=60)
_login_limiter = RateLimiter(max_calls=5, window_seconds=60)
_reset_limiter = RateLimiter(max_calls=3, window_seconds=60)


@router.post("/register", response_model=RegisterResponse)
async def register(
    body: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _register_limiter.check(request)
    return await auth_service.register(body.email, body.name, body.password, session)


@router.get("/verify-email", response_model=AuthTokenResponse)
async def verify_email(
    token: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    return await auth_service.verify_email(token, session)


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _login_limiter.check(request)
    return await auth_service.login(body.email, body.password, session)


@router.post("/google", response_model=AuthTokenResponse)
async def google_login(
    body: GoogleLoginRequest,
    session: AsyncSession = Depends(get_session),
):
    return await auth_service.google_login(body.id_token, session)


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
):
    return await auth_service.refresh_tokens(body.refresh_token, session)


@router.post("/forgot-password", response_model=StatusResponse)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _reset_limiter.check(request)
    await auth_service.request_password_reset(body.email, session)
    return StatusResponse(message="If the email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=StatusResponse)
async def reset_password(
    body: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
):
    await auth_service.reset_password(body.token, body.new_password, session)
    return StatusResponse(message="Password reset successful.")


@router.post("/change-password", response_model=StatusResponse)
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await auth_service.change_password(user.id, body.current_password, body.new_password, session)
    return StatusResponse(message="Password changed successfully.")


@router.get("/me", response_model=UserProfileResponse)
async def me(user: User = Depends(get_current_user)):
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
        auth_method=user.auth_method,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await auth_service.update_profile(user.id, body.name, session)


@router.post("/logout", response_model=StatusResponse)
async def logout(user: User = Depends(get_current_user)):
    return StatusResponse(message="Logged out. Please clear tokens on the client.")
