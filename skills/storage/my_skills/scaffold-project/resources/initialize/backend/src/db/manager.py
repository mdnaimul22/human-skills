from __future__ import annotations
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from src.config import Settings, ensure_dir, setup_logger
from src.db.helpers.base import Base
from src.db.helpers.migrations import SchemaMigrator
from src.db.helpers.registry import active_tables
from src.helpers import ExternalServiceError

logger = setup_logger(Settings.LOG_DIR / "db.log", name="db.manager")

class DatabaseManager:
    _instance: DatabaseManager | None = None
    _initialized: bool = False

    def __new__(cls, database_url: str | None = None, echo: bool = False) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, database_url: str | None = None, echo: bool = False) -> None:
        if self._initialized:
            return
        self._lock = threading.Lock()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._migrator: SchemaMigrator | None = None
        if database_url is not None:
            self.initialize(database_url, echo=echo)
        self._initialized = True

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def initialize(self, database_url: str, echo: bool = False) -> None:
        with self._lock:
            if "sqlite" in database_url:
                ensure_dir(Settings.DATA_DIR)
            self._engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
            self._session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False,
            )
            self._migrator = SchemaMigrator(self._engine)
            logger.info("Database engine & session factory initialized")

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise ExternalServiceError("database", "Database engine not initialized")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise ExternalServiceError("database", "Database session factory not initialized")
        return self._session_factory

    @property
    def orphans(self) -> list[str]:
        return list(self._migrator.last_orphans) if self._migrator is not None else []

    async def create_tables(self, domain_root: str = "src/db/domain") -> None:
        tables = active_tables(domain_root)
        async with self.engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
        logger.info("Database tables verified & created")

    async def migrate(self, domain_root: str = "src/db/domain") -> dict[str, list[str]]:
        if self._migrator is None:
            raise ExternalServiceError("database", "Database migrator not initialized")
        results = await self._migrator.run(domain_root=domain_root)
        logger.info(f"Database schema migrations complete: {results}")
        return results

    async def prune_orphans(self, domain_root: str = "src/db/domain") -> list[str]:
        if self._migrator is None:
            raise ExternalServiceError("database", "Database migrator not initialized")
        return await self._migrator.prune_orphans(domain_root=domain_root)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        factory = self.session_factory
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        factory = self.session_factory
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def ping(self) -> bool:
        if self._engine is None:
            return False
        try:
            async with self.engine.connect() as conn:
                res = await conn.execute(text("SELECT 1"))
                return res.scalar_one() == 1
        except Exception as err:
            logger.warning(f"Database ping failed: {err}")
            return False

    async def shutdown(self) -> None:
        with self._lock:
            if self._engine is not None:
                await self._engine.dispose()
                self._engine = None
                self._session_factory = None
                self._migrator = None
                logger.info("Database engine gracefully shut down")

def get_db_manager() -> DatabaseManager:
    return DatabaseManager()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    mgr = get_db_manager()
    async for session in mgr.get_session():
        yield session

@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    mgr = get_db_manager()
    async with mgr.session_scope() as session:
        yield session

def init_db(database_url: str, echo: bool = False) -> None:
    get_db_manager().initialize(database_url, echo=echo)

async def shutdown_db() -> None:
    await get_db_manager().shutdown()

async def create_tables(domain_root: str = "src/db/domain") -> None:
    await get_db_manager().create_tables(domain_root=domain_root)

async def ensure_schema_migrations(domain_root: str = "src/db/domain") -> dict[str, list[str]]:
    return await get_db_manager().migrate(domain_root=domain_root)
