"""
Database package — connection lifecycle, models, and repositories.

Usage in main.py:
    from src.db import init_db, shutdown_db, create_tables

    async def lifespan(app):
        init_db(Settings.DATABASE_URL)
        await create_tables()
        yield
        await shutdown_db()

Usage in routers / services:
    from src.db import get_session, UserRepository

    @router.get("/me")
    async def me(session: AsyncSession = Depends(get_session)):
        repo = UserRepository(session)
        ...
"""

from .connection import (
    init_db,
    shutdown_db,
    get_session,
    session_scope,
    create_tables,
)
from .models import Base, User, TimestampMixin
from .repository import BaseRepository
from .repositories import UserRepository

__all__ = [
    "init_db",
    "shutdown_db",
    "get_session",
    "session_scope",
    "create_tables",
    "Base",
    "User",
    "TimestampMixin",
    "BaseRepository",
    "UserRepository",
]
