"""
Pytest configuration and test fixtures for FastAPI application.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure initialize directory is in sys.path
INITIALIZE_DIR = Path(__file__).resolve().parent.parent
if str(INITIALIZE_DIR) not in sys.path:
    sys.path.insert(0, str(INITIALIZE_DIR))

# Configure test environment variables before module imports
TEST_DB_FILE = INITIALIZE_DIR / "data" / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
os.environ["APP_ENV"] = "testing"
os.environ["JWT_SECRET"] = "test-secret-key-for-automated-tests"

from src.db import init_db, shutdown_db, create_tables
from src.config import Settings
from main import app


import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    """Initializes isolated database for test session and tears it down afterwards."""
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
    """Async HTTP test client bound to FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
