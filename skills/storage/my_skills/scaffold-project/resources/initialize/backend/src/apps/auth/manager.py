from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hmac
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.auth.helpers.oauth import (
    exchange_google_code_async, get_google_auth_url, refresh_google_access_token_async,
)
from src.apps.auth.helpers.schema import AuthSessionBundle, ProviderCredential
from src.apps.auth.helpers.tokens import (
    create_token, decode_token_claims, issue_refresh_token, parse_refresh_token,
)
from src.apps.auth.helpers.vault import decrypt_secret, encrypt_secret
from src.config import Settings, setup_logger
from src.db import (
    IdentityRepository, RevokedTokenRepository, SessionRepository, UserRepository,
)
from src.helpers import AuthenticationError, ValidationError, get_now_utc

logger = setup_logger(Settings.LOG_DIR / "auth.log", name="apps.auth.manager")
_REFRESH_TTL_DAYS = 30

def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class AuthManager:
    _instance: AuthManager | None = None

    def __new__(cls) -> AuthManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_google_login_url(self, redirect_uri: str | None = None) -> str:
        return get_google_auth_url(redirect_uri=redirect_uri)

    async def login_with_google(
        self, code: str, session: AsyncSession, user_agent: str = "",
    ) -> AuthSessionBundle:
        if not code or not code.strip():
            raise ValidationError("Google authorization code cannot be empty")
        info = await exchange_google_code_async(code.strip())
        google_id = info.get("google_id")
        email = info.get("email")
        if not google_id or not email:
            raise ValidationError("Failed to obtain Google account credentials")
        name = info.get("name") or email.split("@")[0]
        avatar_url = info.get("avatar_url")
        access_enc = encrypt_secret(info.get("access_token"))
        refresh_enc = encrypt_secret(info.get("refresh_token"))
        expires_in = int(info.get("expires_in", 3600))
        now = get_now_utc()
        token_expires_at = now + timedelta(seconds=expires_in)
        user_repo = UserRepository(session)
        user, _ = await user_repo.upsert_oauth_user(
            provider="google", subject=google_id, email=email, name=name,
            avatar_url=avatar_url, access_token_enc=access_enc,
            refresh_token_enc=refresh_enc, token_expires_at=token_expires_at,
        )
        session_id = uuid.uuid4().hex
        raw_refresh, refresh_hash = issue_refresh_token(session_id)
        session_repo = SessionRepository(session)
        await session_repo.create(
            id=session_id, user_id=user.id, refresh_hash=refresh_hash,
            user_agent=user_agent[:255], expires_at=now + timedelta(days=_REFRESH_TTL_DAYS),
        )
        access_jwt = create_token(
            user.id, tier=user.tier, expires_in_seconds=Settings.JWT_EXPIRY_HOURS * 3600,
        )
        logger.info(f"Authenticated Google user: {user.email} ({user.id})")
        return AuthSessionBundle(
            token=access_jwt, access_token=access_jwt, refresh_token=raw_refresh,
            session_id=session_id, user_id=user.id, name=user.name,
            email=user.email, avatar_url=user.avatar_url, tier=user.tier,
        )

    async def refresh_session(
        self, raw_refresh_token: str, session: AsyncSession,
    ) -> AuthSessionBundle:
        session_id, token_hash = parse_refresh_token(raw_refresh_token)
        session_repo = SessionRepository(session)
        record = await session_repo.get(session_id)
        if record is None:
            raise AuthenticationError("Auth session not found")
        if record.revoked_at is not None or not hmac.compare_digest(record.refresh_hash, token_hash):
            await session_repo.revoke_all_for_user(record.user_id)
            logger.warning(f"Refresh token reuse detected for user={record.user_id}; revoked all sessions")
            raise AuthenticationError("Refresh token reuse detected; session revoked")
        now = get_now_utc()
        exp_utc = _ensure_utc(record.expires_at)
        if exp_utc is not None and exp_utc < now:
            await session_repo.revoke(session_id)
            raise AuthenticationError("Refresh session expired")
        user = await UserRepository(session).get(record.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        new_raw_refresh, new_hash = issue_refresh_token(record.id)
        await session_repo.rotate(record, new_hash, now + timedelta(days=_REFRESH_TTL_DAYS))
        access_jwt = create_token(
            user.id, tier=user.tier, expires_in_seconds=Settings.JWT_EXPIRY_HOURS * 3600,
        )
        return AuthSessionBundle(
            token=access_jwt, access_token=access_jwt, refresh_token=new_raw_refresh,
            session_id=record.id, user_id=user.id, name=user.name,
            email=user.email, avatar_url=user.avatar_url, tier=user.tier,
        )

    async def revoke_token(self, token: str, session: AsyncSession) -> None:
        claims = decode_token_claims(token)
        if not claims.jti:
            return
        exp_dt = datetime.fromtimestamp(claims.exp, tz=timezone.utc) if claims.exp else get_now_utc()
        await RevokedTokenRepository(session).revoke(claims.jti, claims.sub, exp_dt)

    async def revoke_session(self, session_id: str, session: AsyncSession) -> None:
        await SessionRepository(session).revoke(session_id)

    async def provider_credential(
        self, user_id: str, provider: str,
        session: AsyncSession, auto_refresh: bool = True,
    ) -> ProviderCredential | None:
        ident_repo = IdentityRepository(session)
        identity = await ident_repo.find_for_user(user_id, provider)
        if identity is None:
            return None
        access_token = decrypt_secret(identity.access_token_enc)
        refresh_token = decrypt_secret(identity.refresh_token_enc)
        exp_utc = _ensure_utc(identity.token_expires_at)
        now = get_now_utc()
        if auto_refresh and refresh_token and provider == "google":
            if exp_utc is not None and exp_utc <= now + timedelta(seconds=60):
                try:
                    refreshed = await refresh_google_access_token_async(refresh_token)
                    new_access = refreshed.get("access_token")
                    new_exp_in = int(refreshed.get("expires_in", 3600))
                    if new_access:
                        access_token = new_access
                        exp_utc = now + timedelta(seconds=new_exp_in)
                        identity.access_token_enc = encrypt_secret(new_access)
                        identity.token_expires_at = exp_utc
                        await session.commit()
                except Exception as exc:
                    logger.warning(f"Failed to auto-refresh {provider} credential for user={user_id}: {exc}")
        return ProviderCredential(
            provider=provider, subject=identity.subject,
            access_token=access_token, expires_at=exp_utc,
        )

def get_auth_manager() -> AuthManager:
    return AuthManager()
