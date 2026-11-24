from datetime import timedelta
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.db import Base, load_metadata
from src.db.system import (
    IdentityRepository,
    RevokedTokenRepository,
    SessionRepository,
    UserRepository,
)
from src.helpers import get_now_utc


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    load_metadata()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_user_and_identity_repositories(db_session: AsyncSession):
    repo = UserRepository(db_session)
    user = await repo.upsert_google_user(
        google_id="gid_123",
        email="test@example.com",
        name="Test User",
        avatar_url="https://example.com/avatar.png",
    )
    assert user.email == "test@example.com"

    by_email = await repo.find_by_email("TEST@example.com")
    assert by_email is not None
    assert by_email.id == user.id

    by_gid = await repo.find_by_google_id("gid_123")
    assert by_gid is not None
    assert by_gid.id == user.id

    ident = await IdentityRepository(db_session).find("google", "gid_123")
    assert ident is not None
    assert ident.user_id == user.id

    updated = await repo.upsert_google_user(
        google_id="gid_123",
        email="test@example.com",
        name="Updated Name",
    )
    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_session_and_revoked_token_repositories(db_session: AsyncSession):
    user = await UserRepository(db_session).upsert_google_user("gid_sess", "sess@example.com", "Session User")
    now = get_now_utc()

    sess_repo = SessionRepository(db_session)
    sess = await sess_repo.create(
        id="sess_001",
        user_id=user.id,
        refresh_hash="hash_initial_123",
        user_agent="pytest-client",
        expires_at=now + timedelta(days=7),
    )
    assert sess.id == "sess_001"
    fetched = await sess_repo.get("sess_001")
    assert fetched is not None and fetched.revoked_at is None

    await sess_repo.revoke("sess_001")
    revoked_sess = await sess_repo.get("sess_001")
    assert revoked_sess is not None and revoked_sess.revoked_at is not None

    rev_repo = RevokedTokenRepository(db_session)
    assert await rev_repo.is_revoked("jti_001") is False
    await rev_repo.revoke("jti_001", user.id, now + timedelta(hours=1))
    assert await rev_repo.is_revoked("jti_001") is True
