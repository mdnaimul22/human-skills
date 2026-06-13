"""
Database package — re-exports connection lifecycle + models + repositories.

Usage in main.py:
    from src.db import init_db, shutdown_db, Base

    async def lifespan(app):
        init_db(Settings.DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        await shutdown_db()

Usage in routers:
    from src.db import get_session, UserRepository

    @router.get("/me")
    async def me(session: AsyncSession = Depends(get_session)):
        repo = UserRepository(session)
        ...
"""

from src.helpers import init_db, get_session, shutdown_db, session_scope
from .models import Base, User
from .repositories import UserRepository

__all__ = [
    "init_db", "get_session", "shutdown_db", "session_scope",
    "Base", "User", "UserRepository",
]
