from __future__ import annotations
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.schema import JobStatus
from src.apps.system import SystemManager
from src.apps.jobs.helpers.job_control import JobControl
from src.apps.jobs.helpers.job_journal import JobRecord
from src.apps.jobs.helpers.live_monitor import LiveMonitor, _is_terminal_payload

def test_is_terminal_payload() -> None:
    assert _is_terminal_payload('{"status": "complete"}')
    assert _is_terminal_payload('{"status": "failed"}')
    assert _is_terminal_payload('{"status": "timeout"}')
    assert _is_terminal_payload('{"status": "tombstone"}')
    assert not _is_terminal_payload('{"status": "processing"}')
    assert not _is_terminal_payload('{"status": "queued"}')
    assert not _is_terminal_payload('invalid json')

@pytest.mark.asyncio
async def test_live_monitor_stream_progress_in_memory() -> None:
    job = JobRecord("mon_job_1", "test_svc", "127.0.0.1")
    control = JobControl(SystemManager.get_instance())
    monitor = LiveMonitor({job.job_id: job}, control)

    events: list[str] = []

    async def consumer() -> None:
        async for chunk in monitor.stream_progress(job.job_id):
            events.append(chunk)

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.02)

    job.update(50, "Halfway", JobStatus.PROCESSING)
    await asyncio.sleep(0.02)

    job.complete("tmp/downloads/out.mp4")
    await asyncio.sleep(0.02)
    await task

    assert len(events) >= 3
    assert any("Halfway" in e for e in events)
    assert "complete" in events[-1]

@pytest.mark.asyncio
async def test_live_monitor_stream_progress_not_found() -> None:
    control = JobControl(SystemManager.get_instance())
    monitor = LiveMonitor({}, control)

    with patch("src.apps.jobs.helpers.live_monitor.get_redis") as mock_get:
        mock_redis = MagicMock()
        mock_redis.is_available = False
        mock_get.return_value = mock_redis

        chunks = [chunk async for chunk in monitor.stream_progress("non_existent_job")]
        assert len(chunks) == 1
        assert "Job not found" in chunks[0]

@pytest.mark.asyncio
async def test_live_monitor_evict_stale_memory_jobs() -> None:
    control = JobControl(SystemManager.get_instance())
    job_stale = JobRecord("stale_job", "svc", "127.0.0.1")
    job_stale.complete("out")
    job_stale.completed_at = time.monotonic() - 7200.0

    job_active = JobRecord("active_job", "svc", "127.0.0.1")

    jobs = {job_stale.job_id: job_stale, job_active.job_id: job_active}
    monitor = LiveMonitor(jobs, control)

    await monitor._evict_stale_memory_jobs()
    assert "stale_job" not in jobs
    assert "active_job" in jobs

@pytest.mark.asyncio
async def test_live_monitor_tombstone_and_zombie_reaper() -> None:
    control = JobControl(SystemManager.get_instance())
    control.reap_expired_tokens = AsyncMock(return_value=["token_reaped_1"])

    job = JobRecord("tombstone_job", "svc", "127.0.0.1")
    job.mark_tombstone(ttl=-10.0)

    jobs = {job.job_id: job}
    monitor = LiveMonitor(jobs, control)

    purged = await monitor._sweep_tombstones()
    assert purged == 1
    assert "tombstone_job" not in jobs

    reaped = await monitor._zombie_lease_reaper()
    assert reaped == ["token_reaped_1"]


@pytest.mark.asyncio
async def test_zombie_reaper_renews_live_processing_job_lease() -> None:
    sm = SystemManager.get_instance()
    control = JobControl(sm)
    permit = await control.acquire_resource_permit("download", "live_long_job")
    assert permit is not None
    try:
        control._active_tokens["live_long_job"] = time.time() - 350.0
        job = JobRecord("live_long_job", "video_download", "127.0.0.1")
        job.status = JobStatus.PROCESSING
        job.started_at = time.monotonic() - 350.0
        monitor = LiveMonitor({"live_long_job": job}, control)

        reaped = await monitor._zombie_lease_reaper()
        assert "live_long_job" not in reaped
        assert "live_long_job" in control._active_tokens
        assert (time.time() - control._active_tokens["live_long_job"]) < 5.0
    finally:
        await control.release_resource_token("live_long_job")

@pytest.mark.asyncio
async def test_live_monitor_start_and_shutdown() -> None:
    control = JobControl(SystemManager.get_instance())
    monitor = LiveMonitor({}, control)

    monitor.start()
    assert monitor._running
    assert len(monitor._tasks) == 3

    await monitor.shutdown()
    assert not monitor._running
    for task in monitor._tasks:
        assert task.cancelled()
