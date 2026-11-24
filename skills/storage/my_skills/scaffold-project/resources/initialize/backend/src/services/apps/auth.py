from __future__ import annotations
from datetime import datetime, timezone
from typing import TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.auth import (
    AuthManager, Principal, create_token, decode_token,
    decode_token_claims, hash_password, verify_password,
)
from src.config import Settings, setup_logger
from src.db import (
    IdentityRepository, RevokedTokenRepository, SessionRepository,
    User, UserIdentity, UserRepository,
)
from src.db.domain import resolve_domain_symbol
from src.helpers import (
    AuthenticationError, ConflictError, NotFoundError,
    PermissionDeniedError, ValidationError, get_now_utc,
)

logger = setup_logger(Settings.LOG_DIR / "service.log", name="services.apps.auth")

class AuthSessionResult(TypedDict):
    token: str
    user_id: str
    name: str
    email: str
    avatar_url: str | None
    tier: str

class AuthTokenBundleResult(TypedDict):
    token: str
    access_token: str
    refresh_token: str
    user_id: str
    name: str
    email: str
    avatar_url: str | None
    tier: str

class RegisterResult(TypedDict):
    user_id: str
    email: str
    name: str
    verification_token: str
    message: str

class UserProfileData(TypedDict):
    id: str
    email: str
    name: str
    avatar_url: str | None
    tier: str
    created_at: datetime
    total_downloads: int
    total_favorites: int

def _build_token_bundle(user: User, refresh_token: str | None = None) -> AuthTokenBundleResult:
    access_jwt = create_token(
        user.id, tier=user.tier, expires_in_seconds=Settings.JWT_EXPIRY_HOURS * 3600,
    )
    refresh_jwt = refresh_token or create_token(
        user.id, tier=user.tier, expires_in_seconds=Settings.JWT_EXPIRY_HOURS * 3600 * 4, token_type="refresh",
    )
    return {
        "token": access_jwt, "access_token": access_jwt, "refresh_token": refresh_jwt,
        "user_id": user.id, "name": user.name, "email": user.email,
        "avatar_url": user.avatar_url, "tier": user.tier,
    }

async def google_login(code: str, session: AsyncSession) -> AuthSessionResult:
    bundle = await AuthManager().login_with_google(code, session)
    return {
        "token": bundle.token, "user_id": bundle.user_id,
        "name": bundle.name, "email": bundle.email,
        "avatar_url": bundle.avatar_url, "tier": bundle.tier,
    }

google_sso_login = google_login

async def register(
    email: str, name: str, password: str,
    session: AsyncSession, referral_code: str | None = None,
) -> RegisterResult:
    clean_email = email.strip().lower()
    clean_name = name.strip()
    if not clean_email or "@" not in clean_email:
        raise ValidationError("Invalid email address")
    if not clean_name:
        raise ValidationError("Name cannot be empty")
    user_repo = UserRepository(session)
    existing = await user_repo.find_by_email(clean_email)
    if existing is not None:
        raise ConflictError(f"Email already registered: {clean_email}")
    pw_hash = hash_password(password)
    user, _ = await user_repo.upsert_oauth_user(
        provider="local", subject=clean_email, email=clean_email,
        name=clean_name, access_token_enc=pw_hash,
    )
    verification_token = create_token(user.id, tier=user.tier, token_type="verify_email")
    logger.info(f"User registered via local auth: {user.email} (id={user.id}, referral={referral_code})")
    return {
        "user_id": user.id, "email": user.email, "name": user.name,
        "verification_token": verification_token,
        "message": "Registration successful. Please verify your email.",
    }

async def verify_email(token: str, session: AsyncSession) -> AuthTokenBundleResult:
    user_id = str(decode_token(token, "verify_email"))
    user_repo = UserRepository(session)
    user = await user_repo.get(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    if user.status != "active":
        await user_repo.update(user.id, status="active")
    logger.info(f"Email verified for user: {user.email}")
    return _build_token_bundle(user)

async def login(email: str, password: str, session: AsyncSession) -> AuthTokenBundleResult:
    clean_email = email.strip().lower()
    user = await UserRepository(session).find_by_email(clean_email)
    if user is None:
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise PermissionDeniedError("Account is inactive")
    identity = await IdentityRepository(session).find_for_user(user.id, "local")
    if identity is None or not identity.access_token_enc:
        raise AuthenticationError("Invalid email or password")
    if not verify_password(password, identity.access_token_enc):
        raise AuthenticationError("Invalid email or password")
    logger.info(f"User logged in via local auth: {user.email}")
    return _build_token_bundle(user)

async def refresh_tokens(refresh_token: str, session: AsyncSession) -> AuthTokenBundleResult:
    if "." in refresh_token and refresh_token.count(".") == 1:
        bundle = await AuthManager().refresh_session(refresh_token, session)
        return {
            "token": bundle.token, "access_token": bundle.access_token,
            "refresh_token": bundle.refresh_token, "user_id": bundle.user_id,
            "name": bundle.name, "email": bundle.email,
            "avatar_url": bundle.avatar_url, "tier": bundle.tier,
        }
    claims = decode_token_claims(refresh_token, "refresh")
    if not claims.jti:
        raise AuthenticationError("Invalid token: missing token identifier")
    revoked_repo = RevokedTokenRepository(session)
    if await revoked_repo.is_revoked(claims.jti):
        raise AuthenticationError("Token has been revoked")
    user = await UserRepository(session).get(claims.sub)
    if user is None:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise PermissionDeniedError("Account is inactive")
    exp_dt = datetime.fromtimestamp(claims.exp, tz=timezone.utc) if claims.exp else get_now_utc()
    await revoked_repo.revoke(claims.jti, user.id, exp_dt)
    return _build_token_bundle(user)

async def logout(refresh_token: str, actor_user_id: str, session: AsyncSession) -> None:
    if "." in refresh_token and refresh_token.count(".") == 1:
        session_id = refresh_token.split(".", 1)[0]
        record = await SessionRepository(session).get(session_id)
        if record is None or record.user_id != actor_user_id:
            raise PermissionDeniedError("Refresh token does not belong to authenticated user")
        await AuthManager().revoke_session(session_id, session)
        return
    claims = decode_token_claims(refresh_token, "refresh")
    if claims.sub != actor_user_id:
        raise PermissionDeniedError("Refresh token does not belong to authenticated user")
    if not claims.jti:
        raise AuthenticationError("Invalid token: missing token identifier")
    exp_dt = datetime.fromtimestamp(claims.exp, tz=timezone.utc) if claims.exp else get_now_utc()
    await RevokedTokenRepository(session).revoke(claims.jti, actor_user_id, exp_dt)

async def purge_expired_revoked_tokens(session: AsyncSession) -> int:
    return await RevokedTokenRepository(session).purge_expired()

async def request_password_reset(email: str, session: AsyncSession) -> str | None:
    user = await UserRepository(session).find_by_email(email.strip().lower())
    if user is None:
        return None
    identity = await IdentityRepository(session).find_for_user(user.id, "local")
    if identity is None:
        return None
    reset_token = create_token(user.id, tier=user.tier, token_type="reset_password")
    logger.info(f"Password reset token issued for: {user.email}")
    return reset_token

async def reset_password(token: str, new_password: str, session: AsyncSession) -> None:
    user_id = str(decode_token(token, "reset_password"))
    user = await UserRepository(session).get(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    ident_repo = IdentityRepository(session)
    identity = await ident_repo.find_for_user(user.id, "local")
    if identity is None:
        raise ValidationError("Cannot reset password for OAuth-only accounts")
    identity.access_token_enc = hash_password(new_password)
    await session.commit()
    logger.info(f"Password reset completed for: {user.email}")

async def change_password(
    user_id: str, current_password: str, new_password: str, session: AsyncSession,
) -> None:
    user = await UserRepository(session).get(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    identity = await IdentityRepository(session).find_for_user(user.id, "local")
    if identity is None or not identity.access_token_enc:
        raise ValidationError("Cannot change password for OAuth-only accounts")
    if not verify_password(current_password, identity.access_token_enc):
        raise AuthenticationError("Current password is incorrect")
    identity.access_token_enc = hash_password(new_password)
    await session.commit()
    logger.info(f"Password changed for: {user.email}")

async def _resolve_domain_counts(user_id: str, session: AsyncSession) -> tuple[int, int]:
    total_downloads = 0
    total_favorites = 0
    try:
        hist_cls = resolve_domain_symbol("HistoryRepository")
        total_downloads = await hist_cls(session).count_by_user(user_id)
    except Exception:
        total_downloads = 0
    try:
        fav_cls = resolve_domain_symbol("FavoriteRepository")
        favorites = await fav_cls(session).list_by_user(user_id)
        total_favorites = len(favorites)
    except Exception:
        total_favorites = 0
    return total_downloads, total_favorites

async def get_user_profile(
    user_or_id: str | User | Principal, session: AsyncSession,
) -> UserProfileData:
    if type(user_or_id) is User:
        user: User | None = user_or_id
        lookup_id = user.id
    elif type(user_or_id) is Principal:
        lookup_id = user_or_id.user_id
        user = await UserRepository(session).get(lookup_id)
    else:
        lookup_id = str(user_or_id)
        user = await UserRepository(session).get(lookup_id)
    if user is None:
        raise NotFoundError("User", lookup_id)
    total_downloads, total_favorites = await _resolve_domain_counts(user.id, session)
    return {
        "id": user.id, "email": user.email, "name": user.name,
        "avatar_url": user.avatar_url, "tier": user.tier,
        "created_at": user.created_at, "total_downloads": total_downloads,
        "total_favorites": total_favorites,
    }

async def update_profile(
    user_id: str, name: str, session: AsyncSession,
) -> UserProfileData:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationError("Name cannot be empty")
    updated = await UserRepository(session).update(user_id, name=clean_name)
    if updated is None:
        raise NotFoundError("User", user_id)
    return await get_user_profile(updated, session)
