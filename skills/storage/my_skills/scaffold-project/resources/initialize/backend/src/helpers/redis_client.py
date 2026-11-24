from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Optional

import redis.asyncio as aioredis
from src.config import Settings, setup_logger

logger = setup_logger(Settings.LOG_DIR / "helpers.log", name="helpers.redis")


class RedisManager:
    _instance: Optional[RedisManager] = None

    def __init__(self) -> None:
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._enabled: bool = Settings.REDIS_ENABLED
        self._url: str = Settings.REDIS_URL

    @classmethod
    def get_instance(cls) -> RedisManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_client(self) -> Optional[aioredis.Redis]:
        if not self._enabled:
            return None
        current_loop = None
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self._client is not None and self._loop is current_loop:
            return self._client

        self._loop = current_loop
        self._pool = aioredis.ConnectionPool.from_url(
            self._url,
            max_connections=Settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )
        self._client = aioredis.Redis(connection_pool=self._pool)
        return self._client

    @property
    def is_available(self) -> bool:
        if not self._enabled:
            return False
        return self._get_client() is not None

    async def init(self) -> None:
        if not self._enabled:
            logger.info("Redis is disabled via configuration")
            return
        client = self._get_client()
        if not client:
            from src.helpers.exceptions import ExternalServiceError
            raise ExternalServiceError("Redis", "Redis client could not be created")
        last_err: Exception | None = None
        for attempt in range(1, 4):
            try:
                await client.ping()
                logger.info("Connected to Redis successfully: %s", self._url.split("@")[-1])
                return
            except Exception as e:
                last_err = e
                if attempt < 3:
                    await asyncio.sleep(0.5)
        logger.error("Redis initialization failed on %s: %s", self._url, last_err)
        self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        from src.helpers.exceptions import ExternalServiceError
        raise ExternalServiceError("Redis", f"Redis connection failed: {last_err}")

    async def shutdown(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except Exception as e:
                logger.debug("Error closing Redis client: %s", e)
            self._client = None
        if self._pool:
            try:
                await self._pool.disconnect()
            except Exception as e:
                logger.debug("Error disconnecting Redis pool: %s", e)
            self._pool = None
        logger.info("Redis shutdown complete")

    async def get(self, key: str) -> Optional[str]:
        client = self._get_client()
        if not client:
            return None
        try:
            return await client.get(key)
        except Exception as e:
            logger.debug("Redis get error for %s: %s", key, e)
            return None

    async def set_val(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        nx: bool = False,
    ) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            res = await client.set(key, value, ex=ex, nx=nx)
            return bool(res)
        except Exception as e:
            logger.debug("Redis set error for %s: %s", key, e)
            return False

    set = set_val

    async def get_json(self, key: str) -> Optional[dict]:
        raw = await self.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception as e:
            logger.debug("Redis json decode error for %s: %s", key, e)
            return None

    async def set_json(
        self,
        key: str,
        value: dict | list,
        ex: Optional[int] = None,
        nx: bool = False,
    ) -> bool:
        try:
            raw = json.dumps(value, ensure_ascii=False)
            return await self.set(key, raw, ex=ex, nx=nx)
        except Exception as e:
            logger.debug("Redis json encode error for %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            return bool(await client.delete(key))
        except Exception as e:
            logger.debug("Redis delete error for %s: %s", key, e)
            return False

    async def acquire_dedup(
        self,
        key: str,
        value: str,
        ex: int = 600,
    ) -> tuple[bool, Optional[str]]:
        client = self._get_client()
        if not client:
            return True, value
        script = """
        local current = redis.call('GET', KEYS[1])
        if current then
            return {0, current}
        else
            redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
            return {1, ARGV[1]}
        end
        """
        try:
            res = await client.eval(script, 1, key, value, str(ex))
            match res:
                case [success_val, owner_val]:
                    owner = str(owner_val) if owner_val is not None else None
                    return bool(success_val), owner
                case _:
                    return False, None
        except Exception as e:
            logger.debug("Redis acquire_dedup error for %s: %s", key, e)
            return True, value

    async def release_dedup(self, key: str, expected_value: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        script = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end
        """
        try:
            res = await client.eval(script, 1, key, expected_value)
            return bool(res)
        except Exception as e:
            logger.debug("Redis release_dedup error for %s: %s", key, e)
            return False

    async def set_state(self, job_id: str, state_json: str, ex: int = 3600) -> bool:
        return await self.set(f"job:state:{job_id}", state_json, ex=ex)

    async def get_state(self, job_id: str) -> Optional[str]:
        return await self.get(f"job:state:{job_id}")

    async def publish(self, channel: str, message: str) -> int:
        client = self._get_client()
        if not client:
            return 0
        try:
            return await client.publish(channel, message)
        except Exception as e:
            logger.debug("Redis publish error on %s: %s", channel, e)
            return 0

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        client = self._get_client()
        if not client:
            return
        pubsub = client.pubsub()
        try:
            await pubsub.subscribe(channel)
            while True:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    data = msg.get("data")
                    if data is not None:
                        yield str(data)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.debug("Redis subscribe error on %s: %s", channel, e)
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
            except Exception as close_err:
                logger.debug("Pubsub close error: %s", close_err)


def get_redis() -> RedisManager:
    return RedisManager.get_instance()


async def init_redis() -> None:
    await get_redis().init()


async def shutdown_redis() -> None:
    await get_redis().shutdown()
