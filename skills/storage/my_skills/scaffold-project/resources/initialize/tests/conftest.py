from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

INITIALIZE_DIR = Path(__file__).resolve().parent.parent
if str(INITIALIZE_DIR) not in sys.path:
    sys.path.insert(0, str(INITIALIZE_DIR))

TEST_DB_FILE = INITIALIZE_DIR / "data" / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
os.environ["APP_ENV"] = "testing"
os.environ["JWT_SECRET"] = "test-secret-key-for-automated-tests"

from src.db import init_db, shutdown_db, create_tables, get_session
from src.config import Settings
from src.routers.auth import _register_limiter, _login_limiter, _reset_limiter
from main import app

from httpx import AsyncClient, ASGITransport
import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    _register_limiter.reset()
    _login_limiter.reset()
    _reset_limiter.reset()
    TEST_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    init_db(f"sqlite+aiosqlite:///{TEST_DB_FILE}")
    await create_tables()
    yield
    await shutdown_db()
    if TEST_DB_FILE.exists():
        try:
            TEST_DB_FILE.unlink()
        except OSError:
            pass


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async for session in get_session():
        yield session
