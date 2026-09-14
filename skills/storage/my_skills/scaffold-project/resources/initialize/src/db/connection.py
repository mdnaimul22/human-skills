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

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.helpers import ExternalServiceError

class DatabaseManager:
    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int | None = None,
        max_overflow: int | None = None,
    ) -> None:
        engine_kwargs: dict = {
            "echo": echo,
            "pool_pre_ping": True,
        }
        if "sqlite" not in database_url and pool_size is not None:
            engine_kwargs["pool_size"] = pool_size
            if max_overflow is not None:
                engine_kwargs["max_overflow"] = max_overflow

        self.engine = create_async_engine(database_url, **engine_kwargs)

        if "sqlite" in database_url:
            @event.listens_for(self.engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self, base_metadata=None) -> None:
        if self.engine is None:
            raise ExternalServiceError("Database", "Database not initialized. Call init_db() first.")
        if base_metadata is None:
            from src.db.models import Base
            base_metadata = Base.metadata
        async with self.engine.begin() as conn:
            await conn.run_sync(base_metadata.create_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.session_factory is None:
            raise ExternalServiceError("Database", "Database not initialized. Call init_db() first.")

        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def shutdown(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        if self.session_factory is None:
            raise ExternalServiceError("Database", "Database not initialized. Call init_db() first.")
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


db_manager = DatabaseManager()
init_db = db_manager.init
create_tables = db_manager.create_tables
get_session = db_manager.get_session
shutdown_db = db_manager.shutdown
session_scope = db_manager.session_scope
