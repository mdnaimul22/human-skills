from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.helpers.exceptions import ExternalServiceError
from src.helpers.redis_client import RedisManager


@pytest.mark.asyncio
async def test_redis_init_when_disabled() -> None:
    mgr = RedisManager()
    mgr._enabled = False
    await mgr.init()
    assert mgr._client is None


@pytest.mark.asyncio
async def test_redis_init_success() -> None:
    mgr = RedisManager()
    mgr._enabled = True
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    with patch.object(mgr, "_get_client", return_value=mock_client):
        await mgr.init()
        mock_client.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_init_fails_fast_without_fallback() -> None:
    mgr = RedisManager()
    mgr._enabled = True
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))
    with patch.object(mgr, "_get_client", return_value=mock_client):
        with pytest.raises(ExternalServiceError) as exc_info:
            await mgr.init()
        assert "Redis connection failed" in str(exc_info.value)
        assert mgr._client is None


@pytest.mark.asyncio
async def test_redis_get_and_set() -> None:
    mgr = RedisManager()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value="val123")
    mock_client.set = AsyncMock(return_value=True)
    with patch.object(mgr, "_get_client", return_value=mock_client):
        val = await mgr.get("key1")
        assert val == "val123"
        res = await mgr.set_val("key1", "val123")
        assert res is True


@pytest.mark.asyncio
async def test_redis_acquire_dedup() -> None:
    mgr = RedisManager()
    mock_client = AsyncMock()
    mock_client.eval = AsyncMock(return_value=[1, "worker1"])
    with patch.object(mgr, "_get_client", return_value=mock_client):
        success, owner = await mgr.acquire_dedup("lock_key", "worker1")
        assert success is True
        assert owner == "worker1"


@pytest.mark.asyncio
async def test_redis_shutdown() -> None:
    mgr = RedisManager()
    mock_client = AsyncMock()
    mock_pool = AsyncMock()
    mgr._client = mock_client
    mgr._pool = mock_pool
    await mgr.shutdown()
    mock_client.aclose.assert_awaited_once()
    mock_pool.disconnect.assert_awaited_once()
    assert mgr._client is None
    assert mgr._pool is None

