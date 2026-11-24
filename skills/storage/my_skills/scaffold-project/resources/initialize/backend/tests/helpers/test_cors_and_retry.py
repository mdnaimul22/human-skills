from __future__ import annotations

from dataclasses import dataclass
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.helpers.cors import register_cors
from src.helpers.retry import retry_async_on_failure, retry_on_failure


@dataclass
class DummyCorsSettings:
    is_development: bool = True
    API_PORT: int = 8000
    FRONTEND_URL: str = "https://example.com/"
    EXTRA_CORS_ORIGINS: str = "https://a.example.com/, https://b.example.com"


def test_register_cors_attaches_middleware_cleanly() -> None:
    app = FastAPI()
    register_cors(app, DummyCorsSettings())

    @app.get("/ping")
    def _ping() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.options(
        "/ping",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://example.com"


def test_retry_on_failure_sync() -> None:
    attempts = 0

    @retry_on_failure(max_attempts=3, initial_wait=0.01, max_wait=0.02)
    def _flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("transient failure")
        return "recovered"

    assert _flaky() == "recovered"
    assert attempts == 2


@pytest.mark.asyncio
async def test_retry_async_on_failure() -> None:
    attempts = 0

    @retry_async_on_failure(max_attempts=3, initial_wait=0.01, max_wait=0.02)
    async def _flaky_async() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise TimeoutError("transient async timeout")
        return "async_recovered"

    assert await _flaky_async() == "async_recovered"
    assert attempts == 2
