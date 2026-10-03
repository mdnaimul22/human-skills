from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import BaseRepository
from src.db.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(self.model).where(self.model.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_google_id(self, google_id: str) -> User | None:
        stmt = select(self.model).where(self.model.google_id == google_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, email: str, name: str, password_hash: str) -> User:
        return await self.create(
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=password_hash,
        )

    async def create_google_user(self, email: str, name: str, google_id: str) -> User:
        return await self.create(
            email=email.lower().strip(),
            name=name.strip(),
            google_id=google_id,
            auth_method="google",
            email_verified=True,
        )

    async def set_email_verified(self, user_id: str) -> User | None:
        return await self.update(user_id, email_verified=True)

    async def update_password(self, user_id: str, password_hash: str) -> User | None:
        return await self.update(user_id, password_hash=password_hash)

    async def update_profile(self, user_id: str, name: str) -> User | None:
        return await self.update(user_id, name=name.strip())
