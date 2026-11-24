from __future__ import annotations
import asyncio
import shutil
import time
from collections import defaultdict
from types import TracebackType
from typing import Optional
from src.config import Settings, setup_logger, exists, get_abs_path
from src.helpers import AppError, ExternalServiceError, RateLimitError, get_redis
from src.apps.system import ResourceLease, ResourcePermit, SystemManager, UserTier

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="apps.jobs.control")

def _positive_int(value: int | float | str | None, default: int) -> int:
    try:
        val = int(value)
        return val if val > 0 else default
    except (TypeError, ValueError):
        return default

class StateLock:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.generation_id: int = 0

    @property
    def is_locked(self) -> bool:
        return self._lock.locked()

    async def __aenter__(self) -> int:
        await self._lock.acquire()
        self.generation_id += 1
        return self.generation_id

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._lock.release()

class JobControl:
    def __init__(self, system_manager: SystemManager) -> None:
        if system_manager is None:
            raise ExternalServiceError("system", "SystemManager is strictly required and cannot be None")
        self.lock = asyncio.Lock()
        self.state_lock = StateLock()
        self.system_manager = system_manager
        self.download_sem = asyncio.Semaphore(_positive_int(Settings.MAX_CONCURRENT_DOWNLOADS, 10))
        self.encode_sem = asyncio.Semaphore(_positive_int(Settings.MAX_CONCURRENT_ENCODES, 2))
        self.global_sem = asyncio.Semaphore(_positive_int(Settings.MAX_QUEUE_DEPTH, 35))
        self.ip_active: dict[str, int] = defaultdict(int)
        self.user_active: dict[str, int] = defaultdict(int)
        self.dedup_index: dict[str, str] = {}
        self._governor_leases: dict[str, ResourceLease] = {}
        self._active_tokens: dict[str, float] = {}

    @property
    def active_tokens(self) -> int:
        return len(self._active_tokens)

    async def acquire_resource_permit(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 3.0,
    ) -> Optional[ResourcePermit]:
        try:
            permit = await self.system_manager.acquire_resource_permit(
                workload_type=workload_type,
                job_id=job_id,
                user_tier=user_tier,
                timeout=timeout,
            )
            async with self.lock:
                self._active_tokens[job_id] = time.time()
                if permit.lease is not None:
                    self._governor_leases[job_id] = permit.lease
            return permit
        except (asyncio.TimeoutError, AppError) as e:
            logger.warning(f"Resource permit acquisition rejected for {job_id} ({workload_type}): {e}")
            return None
        except Exception as e:
            logger.error(f"Resource permit acquisition failed for {job_id} ({workload_type}): {e}")
            return None

    async def acquire_resource_token(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 3.0,
    ) -> Optional[ResourceLease]:
        try:
            lease = await self.system_manager.acquire_permit(
                workload_type=workload_type,
                job_id=job_id,
                user_tier=user_tier,
                timeout=timeout,
            )
            async with self.lock:
                self._active_tokens[job_id] = time.time()
                self._governor_leases[job_id] = lease
            return lease
        except (asyncio.TimeoutError, AppError) as e:
            logger.warning(f"Governor permit acquisition rejected for {job_id} ({workload_type}): {e}")
            return None
        except Exception as e:
            logger.error(f"Resource token acquisition failed for {job_id} ({workload_type}): {e}")
            return None

    async def release_resource_token(self, job_id: str) -> None:
        lease: Optional[ResourceLease] = None
        async with self.lock:
            self._active_tokens.pop(job_id, None)
            lease = self._governor_leases.pop(job_id, None)
        if lease is not None:
            try:
                self.system_manager.release_permit(lease)
            except Exception as e:
                logger.debug(f"Governor release bypassed for {job_id}: {e}")

    async def renew_active_tokens(self, job_ids: set[str], ttl: float = 300.0) -> int:
        if not job_ids:
            return 0
        now = time.time()
        renewed = 0
        async with self.lock:
            for jid in job_ids:
                if jid in self._active_tokens:
                    self._active_tokens[jid] = now
                    lease = self._governor_leases.get(jid)
                    if lease is not None and not lease.released:
                        lease.expires_at = max(lease.expires_at, now + ttl)
                    renewed += 1
        return renewed

    async def reap_expired_tokens(self, ttl: float = 300.0) -> list[str]:
        now = time.time()
        reaped: list[str] = []
        leases_to_release: list[ResourceLease] = []
        async with self.lock:
            for jid, leased_at in list(self._active_tokens.items()):
                if now - leased_at > ttl:
                    reaped.append(jid)
                    self._active_tokens.pop(jid, None)
                    lease = self._governor_leases.pop(jid, None)
                    if lease is not None:
                        leases_to_release.append(lease)
        for l in leases_to_release:
            try:
                self.system_manager.release_permit(l)
            except Exception as e:
                logger.debug(f"Governor permit reap release: {e}")
        try:
            self.system_manager.reap_expired_leases()
        except Exception as e:
            logger.debug(f"Governor reap error: {e}")
        return reaped

    def check_capacity(
        self,
        client_ip: str,
        user_id: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> None:
        ip_limit = Settings.MAX_ACTIVE_JOBS_PER_IP
        if self.ip_active[client_ip] >= ip_limit:
            raise RateLimitError(f"Too many active jobs for IP ({ip_limit} max)")
        base_user_limit = Settings.MAX_USER_CONCURRENT_JOBS
        clean_tier = (tier or "").lower().strip()
        if clean_tier == "registered":
            limit = max(10, base_user_limit)
        elif clean_tier == "premium":
            limit = max(25, base_user_limit * 2)
        else:
            limit = max(10, ip_limit)
        if user_id:
            if self.user_active[user_id] >= limit:
                raise RateLimitError(f"Too many active jobs ({limit} max for {tier or 'registered'})")
        else:
            if self.ip_active[client_ip] >= limit:
                raise RateLimitError(f"Too many active jobs ({limit} max for guest)")
        if not self.global_sem._value:
            raise RateLimitError(f"Queue full ({Settings.MAX_QUEUE_DEPTH} max). Try later.")
        temp_path = "tmp/downloads"
        if exists(temp_path):
            temp_abs = get_abs_path(temp_path)
            free_gb = shutil.disk_usage(temp_abs).free / (1024 ** 3)
            if free_gb < 2.0:
                raise AppError(f"Low disk space: {free_gb:.1f} GB free", status_code=503)

    def record_active_job(
        self,
        client_ip: str,
        content_hash: Optional[str],
        job_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        self.ip_active[client_ip] += 1
        if user_id:
            self.user_active[user_id] += 1
        if content_hash:
            self.dedup_index[content_hash] = job_id

    async def register_submission(
        self,
        client_ip: str,
        content_hash: Optional[str],
        job_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        async with self.lock:
            self.record_active_job(client_ip, content_hash, job_id, user_id=user_id)

    async def release_job(
        self,
        client_ip: str,
        content_hash: Optional[str],
        job_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        async with self.lock:
            self.ip_active[client_ip] = max(0, self.ip_active[client_ip] - 1)
            if user_id:
                self.user_active[user_id] = max(0, self.user_active[user_id] - 1)
            if content_hash:
                current_owner = self.dedup_index.get(content_hash)
                if job_id is None or current_owner == job_id:
                    self.dedup_index.pop(content_hash, None)
                redis = get_redis()
                if redis.is_available:
                    if job_id:
                        await redis.release_dedup(f"job:dedup:{content_hash}", job_id)
                    else:
                        await redis.delete(f"job:dedup:{content_hash}")
        if job_id:
            await self.release_resource_token(job_id)
