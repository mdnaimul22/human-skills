import pytest
import pytest_asyncio
from sqlalchemy import Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from src.db.helpers.store import BaseStore

class DummyBase(DeclarativeBase):
    pass

class DummyItem(DummyBase):
    __tablename__ = "dummy_items"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    value: Mapped[int] = mapped_column(Integer, default=0)

@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(DummyBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_base_store_crud(async_session: AsyncSession):
    repo = BaseStore[DummyItem](DummyItem, async_session)

    created = await repo.create(id="itm_1", name="Alpha", value=10)
    assert created.id == "itm_1"
    assert created.name == "Alpha"

    fetched = await repo.get("itm_1")
    assert fetched is not None
    assert fetched.value == 10

    exists = await repo.exists("itm_1")
    assert exists is True

    not_exists = await repo.exists("itm_99")
    assert not_exists is False

    count = await repo.count()
    assert count == 1

    updated = await repo.update("itm_1", value=25)
    assert updated is not None
    assert updated.value == 25

    all_items = await repo.get_all(limit=10)
    assert len(all_items) == 1

    deleted = await repo.delete("itm_1")
    assert deleted is True

    re_fetched = await repo.get("itm_1")
    assert re_fetched is None

    delete_missing = await repo.delete("missing")
    assert delete_missing is False

    update_missing = await repo.update("missing", value=100)
    assert update_missing is None
