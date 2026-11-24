import pytest
from sqlalchemy import text
from src.db.manager import DatabaseManager, get_db_manager, get_session, session_scope
from src.helpers import ExternalServiceError

@pytest.fixture(autouse=True)
def clean_manager_singleton():
    DatabaseManager.reset_instance()
    yield
    DatabaseManager.reset_instance()

def test_manager_singleton_identity():
    m1 = DatabaseManager()
    m2 = DatabaseManager()
    assert m1 is m2
    assert get_db_manager() is m1

def test_uninitialized_manager_raises():
    mgr = DatabaseManager()
    with pytest.raises(ExternalServiceError):
        _ = mgr.engine
    with pytest.raises(ExternalServiceError):
        _ = mgr.session_factory

@pytest.mark.asyncio
async def test_manager_lifecycle_and_sessions():
    mgr = DatabaseManager()
    mgr.initialize("sqlite+aiosqlite:///:memory:")

    assert await mgr.ping() is True

    await mgr.create_tables()
    migrations = await mgr.migrate()
    assert isinstance(migrations, dict)

    async for session in mgr.get_session():
        res = await session.execute(text("SELECT 100"))
        assert res.scalar_one() == 100

    async with mgr.session_scope() as session:
        res = await session.execute(text("SELECT 200"))
        assert res.scalar_one() == 200

    await mgr.shutdown()
    assert await mgr.ping() is False
