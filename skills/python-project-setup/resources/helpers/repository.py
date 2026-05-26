"""
Base Repository — Generic Async CRUD
=======================================
Extend this class per model to get instant create/read/update/delete.

Usage:
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    from src.db import BaseRepository

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]
        email: Mapped[str]

    class UserRepository(BaseRepository[User]):
        def __init__(self, session):
            super().__init__(User, session)

    # In a router:
    repo = UserRepository(session)
    user = await repo.create(name="Naimul", email="naimul@example.com")
    users = await repo.list(limit=20)
    user = await repo.get(1)
    user = await repo.update(1, name="Updated Name")
    deleted = await repo.delete(1)
"""

from typing import TypeVar, Generic, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic async CRUD repository.

    Provides:
        get(id)                     → single record or None
        list(limit, offset)         → paginated list
        count()                     → total record count
        create(**kwargs)            → insert and return new record
        update(id, **kwargs)        → partial update and return
        delete(id)                  → hard delete, returns bool
        exists(id)                  → check existence without loading

    Extend per model:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session):
                super().__init__(User, session)

            async def find_by_email(self, email: str) -> User | None:
                stmt = select(self.model).where(self.model.email == email)
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()
    """

    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> T | None:
        """Fetch a single record by primary key."""
        return await self.session.get(self.model, id)

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """Fetch a paginated list of records."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Return total number of records."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs) -> T:
        """Insert a new record and return it with refreshed fields."""
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: int, **kwargs) -> T | None:
        """Partial update by primary key. Returns None if not found."""
        obj = await self.get(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        """Hard delete by primary key. Returns False if not found."""
        obj = await self.get(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True

    async def exists(self, id: int) -> bool:
        """Check if a record exists without loading the full object."""
        obj = await self.session.get(self.model, id)
        return obj is not None
