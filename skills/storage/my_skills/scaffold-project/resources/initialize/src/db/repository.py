"""
Base Repository — Generic Async CRUD
=======================================
Extend this class per model to get instant create/read/update/delete.
"""

from typing import TypeVar, Generic, Sequence, Any

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
    """

    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: Any) -> T | None:
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
        """Insert a new record, flush to populate server defaults, and return it."""
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, id: Any, **kwargs) -> T | None:
        """Partial update by primary key. Returns None if not found."""
        obj = await self.get(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.flush()
        return obj

    async def delete(self, id: Any) -> bool:
        """Hard delete by primary key. Returns False if not found."""
        obj = await self.get(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True

    async def exists(self, id: Any) -> bool:
        """Check if a record exists without loading the full object."""
        obj = await self.session.get(self.model, id)
        return obj is not None
