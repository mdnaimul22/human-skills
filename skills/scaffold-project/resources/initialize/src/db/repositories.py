"""
User Repository — extends BaseRepository with auth-specific queries.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers import BaseRepository
from src.db.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def find_by_email(self, email: str) -> User | None:
        """Lookup user by email (case-insensitive)."""
        stmt = select(self.model).where(self.model.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, email: str, name: str, password_hash: str) -> User:
        """Create a new user with pre-hashed password."""
        return await self.create(
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=password_hash,
        )
