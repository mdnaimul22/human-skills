"""
Tests for health and root endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "version" in data
    assert "pid" in data
    assert "active_jobs" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code in (200, 307)
    if response.status_code == 200:
        data = response.json()
        assert data.get("status") == "online"
        assert "name" in data
        assert "version" in data
