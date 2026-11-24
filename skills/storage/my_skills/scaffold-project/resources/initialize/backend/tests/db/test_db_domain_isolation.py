from __future__ import annotations
import sys
import types
import pytest
from sqlalchemy import ForeignKey, String, inspect
from sqlalchemy.orm import Mapped, mapped_column
from src.apps.auth import Principal, create_token, require_principal
from src.config import delete, ensure_dir, write_text
from src.db import Base, DatabaseManager, SchemaMigrator, UserRepository
from src.services import auth_service

@pytest.fixture(autouse=True)
def reset_db_singleton():
    DatabaseManager.reset_instance()
    yield
    DatabaseManager.reset_instance()

@pytest.mark.asyncio
async def test_system_runs_and_authenticates_when_domain_is_deleted():
    mgr = DatabaseManager()
    mgr.initialize("sqlite+aiosqlite:///:memory:")
    await mgr.create_tables(domain_root="src/db/non_existent_domain_dir")
    await mgr.migrate(domain_root="src/db/non_existent_domain_dir")

    async with mgr.engine.connect() as conn:
        table_names = await conn.run_sync(lambda sc: set(inspect(sc).get_table_names()))

    assert "users" in table_names
    assert "user_identities" in table_names
    assert "auth_sessions" in table_names
    assert "revoked_tokens" in table_names
    assert "download_history" not in table_names
    assert "favorite_channels" not in table_names

    async with mgr.session_scope() as session:
        repo = UserRepository(session)
        user = await repo.upsert_google_user(
            google_id="isolated_gid_1", email="isolated@example.com", name="Isolated User",
        )
        token = create_token(user.id, tier=user.tier)
        principal = await require_principal(
            request=None, authorization=f"Bearer {token}", session=session,
        )
        assert type(principal) is Principal
        assert principal.user_id == user.id
        profile = await auth_service.get_user_profile(principal, session)
        assert profile["email"] == "isolated@example.com"
        assert profile["total_downloads"] == 0
        assert profile["total_favorites"] == 0

    await mgr.shutdown()

@pytest.mark.asyncio
async def test_domain_removal_detects_orphans_and_prunes_safely():
    mgr = DatabaseManager()
    mgr.initialize("sqlite+aiosqlite:///:memory:")
    await mgr.create_tables(domain_root="src/db/domain")
    await mgr.migrate(domain_root="src/db/domain")
    assert mgr.orphans == []

    await mgr.migrate(domain_root="src/db/non_existent_domain_dir")
    assert "download_history" in mgr.orphans
    assert "favorite_channels" in mgr.orphans
    assert "users" not in mgr.orphans

    pruned = await mgr.prune_orphans(domain_root="src/db/non_existent_domain_dir")
    assert "download_history" in pruned
    assert mgr.orphans == []

    async with mgr.engine.connect() as conn:
        remaining = await conn.run_sync(lambda sc: set(inspect(sc).get_table_names()))
    assert "users" in remaining
    assert "user_identities" in remaining
    assert "download_history" not in remaining
    await mgr.shutdown()

@pytest.mark.asyncio
async def test_legacy_users_table_migrates_to_user_identities():
    mgr = DatabaseManager()
    mgr.initialize("sqlite+aiosqlite:///:memory:")
    async with mgr.engine.begin() as conn:
        await conn.exec_driver_sql(
            "CREATE TABLE users ("
            "id VARCHAR(32) NOT NULL PRIMARY KEY, "
            "google_id VARCHAR(255) NOT NULL, "
            "email VARCHAR(255) NOT NULL, "
            "name VARCHAR(100) NOT NULL, "
            "avatar_url TEXT, "
            "refresh_token TEXT, "
            "access_token TEXT, "
            "token_expires_at DATETIME, "
            "tier VARCHAR(20) NOT NULL, "
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, "
            "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )
        await conn.exec_driver_sql(
            "INSERT INTO users (id, google_id, email, name, refresh_token, access_token, tier) "
            "VALUES ('u_legacy_1', 'g_legacy_100', 'legacy@example.com', 'Legacy User', 'rt_1', 'at_1', 'registered')"
        )

    migrator = SchemaMigrator(mgr.engine)
    applied = await migrator.run(domain_root="src/db/non_existent_domain_dir")
    assert "users" in applied
    assert "users.identities_migrated" in applied["users"]

    async with mgr.session_scope() as session:
        repo = UserRepository(session)
        found = await repo.find_by_google_id("g_legacy_100")
        assert found is not None
        assert found.id == "u_legacy_1"
        assert found.google_id == "g_legacy_100"
        new_user = await repo.create(email="local@example.com", name="Local User")
        assert new_user.email == "local@example.com"

    await mgr.shutdown()

@pytest.mark.asyncio
async def test_dynamic_new_domain_creation_and_removal_lifecycle():
    sandbox_root = "tmp/test_dynamic_domains"
    cv_pkg_dir = f"{sandbox_root}/cv_builder"
    delete(sandbox_root)
    try:
        ensure_dir(cv_pkg_dir)
        write_text(f"{sandbox_root}/__init__.py", "")
        write_text(f"{cv_pkg_dir}/__init__.py", "")

        class CvDocument(Base):
            __tablename__ = "cv_documents"
            id: Mapped[str] = mapped_column(String(32), primary_key=True)
            user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
            title: Mapped[str] = mapped_column(String(120), nullable=False)

        CvDocument.__module__ = "src.db.domain.cv_builder.models"
        fake_pkg = types.ModuleType("src.db.domain.cv_builder")
        fake_models = types.ModuleType("src.db.domain.cv_builder.models")
        fake_models.__dict__["CvDocument"] = CvDocument
        sys.modules["src.db.domain.cv_builder"] = fake_pkg
        sys.modules["src.db.domain.cv_builder.models"] = fake_models
        write_text(f"{cv_pkg_dir}/models.py", "")

        mgr = DatabaseManager()
        mgr.initialize("sqlite+aiosqlite:///:memory:")
        applied = await mgr.migrate(domain_root=sandbox_root)
        assert "cv_documents" in applied
        assert "users" in applied

        async with mgr.engine.connect() as conn:
            tables_after_add = await conn.run_sync(lambda sc: set(inspect(sc).get_table_names()))
        assert "cv_documents" in tables_after_add
        assert "users" in tables_after_add

        delete(cv_pkg_dir)
        await mgr.migrate(domain_root=sandbox_root)
        assert "cv_documents" in mgr.orphans
        assert "users" not in mgr.orphans

        pruned = await mgr.prune_orphans(domain_root=sandbox_root)
        assert pruned == ["cv_documents"]
        await mgr.shutdown()
    finally:
        delete(sandbox_root)
        if "cv_documents" in Base.metadata.tables:
            Base.metadata.remove(Base.metadata.tables["cv_documents"])
        sys.modules.pop("src.db.domain.cv_builder.models", None)
        sys.modules.pop("src.db.domain.cv_builder", None)
