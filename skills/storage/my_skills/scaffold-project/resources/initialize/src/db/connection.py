"""
Async Database Connection — SQLAlchemy
========================================
Manages async engine lifecycle, session factory, and table initialization.

Requirements:
    pip install sqlalchemy[asyncio] aiosqlite   # SQLite (dev)
    pip install sqlalchemy[asyncio] asyncpg      # PostgreSQL (prod)

Usage in main.py (FastAPI lifespan):
    from src.db import init_db, shutdown_db, create_tables

    @asynccontextmanager
    async def lifespan(app):
        init_db(Settings.DATABASE_URL)
        await create_tables()
        yield
        await shutdown_db()

Usage in routers (dependency injection):
    from src.db import get_session

    @router.get("/users")
    async def list_users(session: AsyncSession = Depends(get_session)):
        repo = UserRepository(session)
        return await repo.list()
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ── Module-level singletons ───────────────────────────────────────────────────
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str, echo: bool = False) -> None:
    """
    Initialize the async engine and session factory.
    Call once at application startup (e.g. in FastAPI lifespan).
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def create_tables(base_metadata=None) -> None:
    """Create all tables defined on Base metadata."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    if base_metadata is None:
        from src.db.models import Base
        base_metadata = Base.metadata
    async with _engine.begin() as conn:
        await conn.run_sync(base_metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — yields a scoped async session per request.

    Usage:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def shutdown_db() -> None:
    """Dispose the engine. Call at application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional scope around a series of operations on a session.
    Automatically commits on success or rolls back on exception.
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
