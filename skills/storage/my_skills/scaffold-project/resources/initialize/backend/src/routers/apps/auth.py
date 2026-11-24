from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import Settings, setup_logger
from src.apps.auth import Principal, get_current_user, get_google_auth_url, verify_oauth_state
from src.db import get_session
from src.helpers import get_allowed_redirect_hosts
from src.helpers.rate_limit import RateLimiter
from src.schema import (
    GoogleAuthUrlResponse, GoogleCallbackRequest, TokenResponse, UserProfileResponse,
)
from src.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
_auth_limiter = RateLimiter(max_calls=10, window_seconds=60)

logger = setup_logger(Settings.LOG_DIR / "router.log", name="routers.apps.auth")


def _resolve_frontend_base(request: Request) -> str:
    raw_host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or ""
    ).strip()
    if raw_host:
        if any(c in raw_host for c in ("@", "/", "\\")) or any(c.isspace() for c in raw_host):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect host")
        if raw_host.lower() not in get_allowed_redirect_hosts(Settings):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect host")

    backend_host = Settings.BACKEND_DOMAIN.lower()
    raw_host_name = raw_host.split(":")[0].lower() if raw_host else ""
    if not raw_host or raw_host.lower() == backend_host or raw_host_name == backend_host:
        return Settings.FRONTEND_URL

    raw_proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "https").lower().strip()
    proto = raw_proto if raw_proto in ("http", "https") else "https"
    return f"{proto}://{raw_host}"


@router.get("/login", response_model=GoogleAuthUrlResponse)
async def get_google_login_url(request: Request):
    _auth_limiter.check(request)
    url = get_google_auth_url()
    return GoogleAuthUrlResponse(url=url)


@router.get("/callback")
async def google_callback_get(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    _auth_limiter.check(request)
    frontend_base = _resolve_frontend_base(request)

    if not code:
        err_type = error or "cancelled"
        return RedirectResponse(url=f"{frontend_base}/login?error={err_type}")

    if not verify_oauth_state(state):
        logger.warning("Rejected Google OAuth callback with missing or invalid state token")
        return RedirectResponse(url=f"{frontend_base}/login?error=invalid_state")

    try:
        result = await auth_service.google_login(code, session)
        token = result["token"]
        frontend_redirect = f"{frontend_base}/login?token={token}"
        redirect_resp = RedirectResponse(url=frontend_redirect)
        redirect_resp.headers["Cache-Control"] = "no-store"
        return redirect_resp
    except Exception as e:
        logger.error(f"Google SSO login failed in callback: {e}")
        return RedirectResponse(url=f"{frontend_base}/login?error=auth_failed")


@router.post("/callback", response_model=TokenResponse)
async def google_callback_post(
    body: GoogleCallbackRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    _auth_limiter.check(request)
    response.headers["Cache-Control"] = "no-store"
    result = await auth_service.google_login(body.code, session)
    return TokenResponse(**result)


@router.get("/me", response_model=UserProfileResponse)
async def me(
    response: Response,
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    response.headers["Cache-Control"] = "no-store"
    profile = await auth_service.get_user_profile(user, session)
    return UserProfileResponse(**profile)
