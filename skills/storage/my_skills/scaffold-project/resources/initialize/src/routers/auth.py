"""
Router — Authentication (Register / Login / Profile).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.schema.auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserProfileResponse,
)
from src.core.auth import get_current_user
from src.db import get_session, User
from src.services import auth as auth_service
from src.helpers.rate_limit import RateLimiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

_register_limiter = RateLimiter(max_calls=3, window_seconds=60)
_login_limiter = RateLimiter(max_calls=5, window_seconds=60)


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, request: Request, session: AsyncSession = Depends(get_session)):
    """Create a new user account."""
    _register_limiter.check(request)
    result = await auth_service.register(body.email, body.name, body.password, session)
    return result


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, session: AsyncSession = Depends(get_session)):
    """Authenticate and get JWT token."""
    _login_limiter.check(request)
    result = await auth_service.login(body.email, body.password, session)
    return result


@router.get("/me", response_model=UserProfileResponse)
async def me(
    user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
    )
