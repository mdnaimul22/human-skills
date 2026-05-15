"""
Async Database Connection — SQLAlchemy
========================================
Manages async engine lifecycle and session factory.

Requirements:
    pip install sqlalchemy[asyncio] aiosqlite   # SQLite (dev)
    pip install sqlalchemy[asyncio] asyncpg      # PostgreSQL (prod)

Usage in main.py (FastAPI lifespan):
    from src.db import init_db, shutdown_db, get_session

    @asynccontextmanager
    async def lifespan(app):
        init_db(Settings.DATABASE_URL)
        yield
        await shutdown_db()

Usage in routers (dependency injection):
    from src.db import get_session

    @router.get("/users")
    async def list_users(session: AsyncSession = Depends(get_session)):
        repo = UserRepository(session)
        return await repo.list()

Settings.py should have:
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/app.db",
        validation_alias="DATABASE_URL"
    )
"""

from typing import AsyncGenerator

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

    Args:
        database_url: Async-compatible connection string.
                      SQLite:     "sqlite+aiosqlite:///./data/app.db"
                      PostgreSQL: "postgresql+asyncpg://user:pass@host/db"
        echo:         If True, log all SQL statements (dev only).
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
