from __future__ import annotations
from datetime import datetime
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.helpers.base import utc_now
from src.db.helpers.store import BaseStore
from src.db.system.models import AuthSession, RevokedToken, User, UserIdentity

class UserRepository(BaseStore[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def find_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.strip().lower()))
        return result.scalar_one_or_none()

    async def find_by_provider(self, provider: str, subject: str) -> User | None:
        stmt = (
            select(User)
            .join(UserIdentity, UserIdentity.user_id == User.id)
            .where(UserIdentity.provider == provider, UserIdentity.subject == subject)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_google_id(self, google_id: str) -> User | None:
        return await self.find_by_provider("google", google_id)

    async def upsert_oauth_user(
        self, provider: str, subject: str, email: str, name: str,
        avatar_url: str | None = None, access_token_enc: str | None = None,
        refresh_token_enc: str | None = None, token_expires_at: datetime | None = None,
    ) -> tuple[User, UserIdentity]:
        clean_email = email.strip().lower()
        clean_name = name.strip()
        ident_repo = IdentityRepository(self.session)
        identity = await ident_repo.find(provider, subject)
        user: User | None = None
        if identity is not None:
            user = await self.get(identity.user_id)
        if user is None:
            user = await self.find_by_email(clean_email)
        if user is None:
            user = User(email=clean_email, name=clean_name, avatar_url=avatar_url, tier="registered", status="active")
            self.session.add(user)
            await self.session.flush()
        else:
            user.name = clean_name
            if avatar_url:
                user.avatar_url = avatar_url
        if identity is None:
            identity = UserIdentity(
                user_id=user.id, provider=provider, subject=subject,
                access_token_enc=access_token_enc, refresh_token_enc=refresh_token_enc,
                token_expires_at=token_expires_at,
            )
            self.session.add(identity)
        else:
            identity.user_id = user.id
            if access_token_enc is not None:
                identity.access_token_enc = access_token_enc
            if refresh_token_enc is not None:
                identity.refresh_token_enc = refresh_token_enc
            if token_expires_at is not None:
                identity.token_expires_at = token_expires_at
        await self.session.commit()
        await self.session.refresh(user)
        await self.session.refresh(identity)
        return user, identity

    async def upsert_google_user(
        self, google_id: str, email: str, name: str,
        avatar_url: str | None = None, refresh_token: str | None = None,
        access_token: str | None = None, token_expires_at: datetime | None = None,
    ) -> User:
        user, _ = await self.upsert_oauth_user(
            provider="google", subject=google_id, email=email, name=name,
            avatar_url=avatar_url, access_token_enc=access_token,
            refresh_token_enc=refresh_token, token_expires_at=token_expires_at,
        )
        return user

class IdentityRepository(BaseStore[UserIdentity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(UserIdentity, session)

    async def find(self, provider: str, subject: str) -> UserIdentity | None:
        stmt = select(UserIdentity).where(UserIdentity.provider == provider, UserIdentity.subject == subject)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_for_user(self, user_id: str, provider: str) -> UserIdentity | None:
        stmt = select(UserIdentity).where(UserIdentity.user_id == user_id, UserIdentity.provider == provider)
        result = await self.session.execute(stmt)
        return result.scalars().first()

class SessionRepository(BaseStore[AuthSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuthSession, session)

    async def find_active(self, session_id: str) -> AuthSession | None:
        record = await self.session.get(AuthSession, session_id)
        if record is None or record.revoked_at is not None:
            return None
        return record

    async def _revoke_matching(self, field_name: str, value: str) -> None:
        target_col = AuthSession.id if field_name == "id" else AuthSession.user_id
        stmt = update(AuthSession).where(target_col == value, AuthSession.revoked_at.is_(None))
        await self.session.execute(stmt.values(revoked_at=utc_now()))
        await self.session.commit()

    async def revoke(self, session_id: str) -> None:
        await self._revoke_matching("id", session_id)

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._revoke_matching("user_id", user_id)

    async def rotate(self, record: AuthSession, refresh_hash: str, expires_at: datetime) -> AuthSession:
        record.refresh_hash = refresh_hash
        record.expires_at = expires_at
        record.last_used_at = utc_now()
        await self.session.commit()
        return record

class RevokedTokenRepository(BaseStore[RevokedToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RevokedToken, session)

    async def is_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        record = await self.get(jti)
        return record is not None

    async def revoke(self, jti: str, user_id: str, expires_at: datetime) -> RevokedToken:
        existing = await self.get(jti)
        if existing is not None:
            return existing
        return await self.create(jti=jti, user_id=user_id, expires_at=expires_at)

    async def purge_expired(self, cutoff: datetime | None = None) -> int:
        ref_time = cutoff or utc_now()
        result = await self.session.execute(delete(RevokedToken).where(RevokedToken.expires_at < ref_time))
        await self.session.commit()
        return int(result.rowcount or 0)
