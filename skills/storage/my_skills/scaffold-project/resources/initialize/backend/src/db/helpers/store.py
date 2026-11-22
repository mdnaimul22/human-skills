from __future__ import annotations
from typing import Generic, Sequence, TypeVar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class BaseStore(Generic[T]):
    def __init__(self, model: type[T], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: str | int) -> T | None:
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, **kwargs: object) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: str | int, **kwargs: object) -> T | None:
        obj = await self.get(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            obj.__setattr__(key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: str | int) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True

    async def exists(self, id: str | int) -> bool:
        obj = await self.session.get(self.model, id)
        return obj is not None
