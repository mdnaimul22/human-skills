"""
Base Repository — Generic Async CRUD
=======================================
Extend this class per model to get instant create/read/update/delete.
"""

from typing import TypeVar, Generic, Sequence

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int | str) -> T | None:
        return await self.session.get(self.model, id)

    async def list_all(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, id: int | str, **kwargs) -> T | None:
        if not kwargs:
            return await self.get(id)
        stmt = update(self.model).filter_by(id=id).values(**kwargs)
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: int | str) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True

    async def exists(self, id: int | str) -> bool:
        obj = await self.session.get(self.model, id)
        return obj is not None
