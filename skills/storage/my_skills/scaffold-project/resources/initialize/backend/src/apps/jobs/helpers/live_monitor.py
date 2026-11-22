from __future__ import annotations
import asyncio
import json
import time
from typing import AsyncGenerator, Awaitable, Callable, Optional
from src.config import Settings, delete, is_dir, job_context, list_files, setup_logger
from src.helpers import get_redis
from src.schema import JobProgress, JobStatus
from .job_control import JobControl
from .job_journal import JobRecord

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="jobs.monitor")

ExpiredCleaner = Callable[[], Awaitable[int]]

def _is_terminal_payload(payload: str) -> bool:
    try:
        parsed = json.loads(payload)
        return parsed.get("status") in ("complete", "failed", "timeout", "tombstone", "purged")
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.debug(f"Terminal payload parse fallback: {exc}")
        return False

async def _ticker_interval(seconds: float) -> None:
    await asyncio.sleep(seconds)

class LiveMonitor:
    def __init__(
        self,
        jobs_registry: dict[str, JobRecord],
        control: JobControl,
        expired_cleaner: Optional[ExpiredCleaner] = None,
    ) -> None:
        self._jobs = jobs_registry
        self.control = control
        self._expired_cleaner = expired_cleaner
        self._running = False
        self._tasks: list[asyncio.Task] = []

    def set_expired_cleaner(self, cleaner: ExpiredCleaner) -> None:
        self._expired_cleaner = cleaner

    def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._cleanup_loop()))
        self._tasks.append(asyncio.create_task(self._timeout_loop()))
        self._tasks.append(asyncio.create_task(self._tombstone_compaction_loop()))
        logger.info("LiveMonitor background tasks started")

    async def shutdown(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        active = [j for j in self._jobs.values() if not j.is_terminal]
        if active:
            logger.info(f"Draining {len(active)} active jobs...")
        logger.info("LiveMonitor shutdown complete")

    async def stream_progress(self, job_id: str) -> AsyncGenerator[str, None]:
        job = self._jobs.get(job_id)
        if not job:
            redis = get_redis()
            if redis.is_available:
                cached = await redis.get_state(job_id)
                if cached:
                    yield f"data: {cached}\n\n"
                    if _is_terminal_payload(cached):
                        return
                async for payload in redis.subscribe(f"job:progress:{job_id}"):
                    yield f"data: {payload}\n\n"
                    if _is_terminal_payload(payload):
                        break
                return
            yield f"data: {JobProgress(job_id=job_id, status=JobStatus.FAILED, error='Job not found').model_dump_json()}\n\n"
            return

        yield f"data: {job.to_progress().model_dump_json()}\n\n"
        if job.is_terminal:
            return

        last_seen = job._update_count
        while not job.is_terminal:
            try:
                await asyncio.wait_for(job._event.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            except asyncio.CancelledError:
                break

            job._event.clear()
            if job._update_count != last_seen:
                last_seen = job._update_count
                yield f"data: {job.to_progress().model_dump_json()}\n\n"

        yield f"data: {job.to_progress().model_dump_json()}\n\n"

    async def _cleanup_loop(self) -> None:
        while self._running:
            await _ticker_interval(300)
            try:
                await self._evict_stale_memory_jobs()
                if self._expired_cleaner:
                    deleted = await self._expired_cleaner()
                    if deleted > 0:
                        logger.info(f"DB cleanup: {deleted} expired files deleted")
                self._sweep_orphan_dirs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _evict_stale_memory_jobs(self) -> None:
        now = time.monotonic()
        stale: list[str] = []
        for jid, job in list(self._jobs.items()):
            if job.is_terminal and (now - (job.completed_at or now)) > Settings.TEMP_FILE_TTL_SECONDS:
                stale.append(jid)
        if not stale:
            return
        async with self.control.lock:
            for jid in stale:
                self._jobs.pop(jid, None)
        logger.info(f"Memory cleanup: {len(stale)} stale jobs evicted")

    def _sweep_orphan_dirs(self) -> None:
        try:
            orphan_count = 0
            for entry in list_files("tmp/downloads", "*"):
                if not is_dir(str(entry)) or entry.name in self._jobs:
                    continue
                try:
                    age_seconds = time.time() - entry.stat().st_mtime
                    if age_seconds <= Settings.PREMIUM_FILE_TTL + 86400:
                        continue
                    delete(f"tmp/downloads/{entry.name}")
                    orphan_count += 1
                except OSError as err:
                    logger.warning(f"Orphan directory removal failed for {entry.name}: {err}")
            if orphan_count:
                logger.info(f"Orphan cleanup: {orphan_count} stale dirs removed")
        except OSError as err:
            logger.debug(f"Orphan cleanup skipped: {err}")

    async def _timeout_loop(self) -> None:
        while self._running:
            await _ticker_interval(30)
            try:
                now = time.monotonic()
                for job in list(self._jobs.values()):
                    if job.status != JobStatus.PROCESSING or not job.started_at:
                        continue
                    if (now - job.started_at) > Settings.JOB_MAX_RUNTIME:
                        job.status = JobStatus.TIMEOUT
                        job.error = "The operation timed out"
                        job.message = job.error
                        job.completed_at = now
                        job._update_count += 1
                        job._signal()
                        with job_context(job.job_id):
                            logger.warning("Timed out")
                        asyncio.create_task(self.control.release_resource_token(job.job_id))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timeout loop error: {e}", exc_info=True)

    async def _sweep_tombstones(self) -> int:
        expired: list[str] = []
        for jid, job in list(self._jobs.items()):
            if job.is_tombstone_expired():
                expired.append(jid)
        if not expired:
            return 0
        async with self.control.lock:
            for jid in expired:
                job = self._jobs.pop(jid, None)
                if job:
                    job.purge()
        return len(expired)

    async def _zombie_lease_reaper(self) -> list[str]:
        return await self.control.reap_expired_tokens(ttl=300.0)

    async def _tombstone_compaction_loop(self) -> None:
        while self._running:
            await _ticker_interval(5)
            try:
                purged = await self._sweep_tombstones()
                if purged > 0:
                    logger.info(f"Tombstone compaction: {purged} tombstones purged")
                reaped = await self._zombie_lease_reaper()
                if reaped:
                    logger.info(f"Zombie lease reaper: {len(reaped)} expired tokens reaped")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Compaction loop error: {e}")
