import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.helpers.migrations import SchemaMigrator
from src.helpers import ValidationError

@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine
    await engine.dispose()

@pytest.mark.asyncio
async def test_schema_migrator_adds_missing_columns(async_engine):
    init_meta = MetaData()
    users_v1 = Table(
        "test_users",
        init_meta,
        Column("id", String(32), primary_key=True),
        Column("username", String(50), nullable=False),
    )
    async with async_engine.begin() as conn:
        await conn.run_sync(init_meta.create_all)
        await conn.exec_driver_sql("INSERT INTO test_users (id, username) VALUES ('u1', 'alice')")

    upgraded_meta = MetaData()
    users_v2 = Table(
        "test_users",
        upgraded_meta,
        Column("id", String(32), primary_key=True),
        Column("username", String(50), nullable=False),
        Column("avatar_url", String(255), nullable=True),
        Column("tier", String(20), server_default="registered"),
    )

    migrator = SchemaMigrator(async_engine)
    applied = await migrator.run(upgraded_meta)

    assert "test_users" in applied
    assert "test_users.avatar_url" in applied["test_users"]
    assert "test_users.tier" in applied["test_users"]

    async with async_engine.connect() as conn:
        res = await conn.exec_driver_sql("SELECT id, username, avatar_url, tier FROM test_users WHERE id='u1'")
        row = res.fetchone()
        assert row is not None
        assert row[0] == "u1"
        assert row[1] == "alice"
        assert row[2] is None
        assert row[3] == "registered"

    applied_again = await migrator.run(upgraded_meta)
    assert applied_again == {}

@pytest.mark.asyncio
async def test_schema_migrator_rejects_invalid_identifier(async_engine):
    migrator = SchemaMigrator(async_engine)
    with pytest.raises(ValidationError):
        migrator._build_alter_sql("users; DROP TABLE x;--", "col", "TEXT", "")
