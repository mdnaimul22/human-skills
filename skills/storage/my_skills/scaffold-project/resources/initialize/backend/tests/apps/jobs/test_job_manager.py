from __future__ import annotations
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.helpers import RateLimitError
from src.schema import JobStatus
from src.apps.system import SystemManager
from src.apps.jobs import JobManager, get_job_manager

from src.config import delete
from src.apps.jobs.helpers import JobRecord

@pytest.fixture(autouse=True)
def clean_env():
    SystemManager.reset_instance()
    JobManager.reset_instance()
    delete("data/jobs_journal.json")
    with patch("src.apps.jobs.helpers.job_submission.get_redis") as mock_redis_sub:
        with patch("src.apps.jobs.helpers.live_monitor.get_redis") as mock_redis_mon:
            mock_r = MagicMock()
            mock_r.is_available = False
            mock_redis_sub.return_value = mock_r
            mock_redis_mon.return_value = mock_r
            yield
    SystemManager.reset_instance()
    JobManager.reset_instance()
    delete("data/jobs_journal.json")

def test_job_manager_singleton_and_factory() -> None:
    mgr1 = get_job_manager()
    mgr2 = JobManager.get_instance()
    assert mgr1 is mgr2

@pytest.mark.asyncio
async def test_job_manager_start_and_shutdown() -> None:
    manager = JobManager()
    await manager.start()
    assert manager.monitor._running

    await manager.shutdown()
    assert not manager.monitor._running

@pytest.mark.asyncio
async def test_job_manager_e2e_submission_and_execution() -> None:
    manager = JobManager()
    await manager.start()

    async def mock_executor(*args, on_progress=None, **kwargs) -> str:
        if on_progress:
            on_progress(50, "Processing task")
        await asyncio.sleep(0.05)
        return "tmp/jobs/e2e_job/result.bin"

    job = await manager.submit(
        job_id="e2e_job_1",
        service_type="batch_task",
        client_ip="192.168.1.50",
        executor=mock_executor,
        workload_type="encode",
        user_id="usr_vip",
    )
    assert job.job_id == "e2e_job_1"
    assert manager.get("e2e_job_1") is job

    while not job.is_terminal:
        await asyncio.wait_for(job._event.wait(), timeout=10.0)
        job._event.clear()
    assert job.status == JobStatus.COMPLETE
    assert job.output_path == "tmp/jobs/e2e_job/result.bin"
    assert manager.active_count() == 0

    await manager.shutdown()

@pytest.mark.asyncio
async def test_job_manager_e2e_deduplication() -> None:
    manager = JobManager()
    await manager.start()

    async def slow_executor(*args, **kwargs) -> str:
        await asyncio.sleep(0.2)
        return "tmp/downloads/dedup/output.mp4"

    job1 = await manager.submit(
        job_id="orig_job",
        service_type="download",
        client_ip="10.0.0.1",
        executor=slow_executor,
        content_hash="canonical_hash_abc",
    )
    job2 = await manager.submit(
        job_id="duplicate_job",
        service_type="download",
        client_ip="10.0.0.1",
        executor=slow_executor,
        content_hash="canonical_hash_abc",
    )
    assert job1 is job2
    assert job2.job_id == "orig_job"

    await manager.shutdown()

@pytest.mark.asyncio
async def test_job_manager_rate_limit_rejection() -> None:
    manager = JobManager()
    manager.control.ip_active["10.0.0.99"] = 50

    async def dummy(*args, **kwargs) -> str:
        return "out"

    with pytest.raises(RateLimitError):
        await manager.submit(
            job_id="blocked_job",
            service_type="download",
            client_ip="10.0.0.99",
            executor=dummy,
        )

    assert manager.get("blocked_job") is None

@pytest.mark.asyncio
async def test_job_manager_stream_progress() -> None:
    manager = JobManager()
    job = await manager.submit(
        job_id="stream_job",
        service_type="download",
        client_ip="127.0.0.1",
        executor=lambda *args, **kwargs: asyncio.sleep(0.01),
    )

    events: list[str] = []

    async def consume() -> None:
        async for chunk in manager.stream_progress("stream_job"):
            events.append(chunk)

    consumer_task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    job.complete("tmp/downloads/final.mp4")
    await consumer_task

    assert len(events) >= 1
    assert "stream_job" in events[-1]


@pytest.mark.asyncio
async def test_job_manager_server_restart_recovery() -> None:
    from src.config import write_text, ensure_dir, exists
    journal_path = "tmp/test_restart_journal.json"
    ensure_dir("tmp/test_downloads/completed_job")
    ensure_dir("tmp/downloads/crashed_job")
    out_file = "tmp/test_downloads/completed_job/final.mp4"
    write_text(out_file, "dummy-video")

    manager1 = JobManager(journal_path=journal_path)
    job_done = JobRecord("completed_job", "download", "127.0.0.1")
    job_done.complete(out_file)
    manager1._jobs["completed_job"] = job_done
    manager1.journal.save_record_sync(job_done.to_dict())

    job_active = JobRecord("in_flight_job", "encode", "127.0.0.1")
    job_active.update(40, "Encoding frame 400", JobStatus.PROCESSING)
    manager1._jobs["in_flight_job"] = job_active
    manager1.journal.save_record_sync(job_active.to_dict())

    # Simulate sudden crash (no graceful shutdown) by writing an in-flight job directly to journal
    job_crash = JobRecord("crashed_job", "download", "127.0.0.1")
    job_crash.update(35, "Downloading media stream", JobStatus.PROCESSING)
    manager1.journal.save_record_sync(job_crash.to_dict())

    await manager1.shutdown()

    manager2 = JobManager(journal_path=journal_path)
    await manager2.start()

    rec_done = manager2.get("completed_job")
    assert rec_done is not None
    assert rec_done.status == JobStatus.COMPLETE
    assert rec_done.output_path == out_file

    rec_active = manager2.get("in_flight_job")
    assert rec_active is not None
    assert rec_active.status == JobStatus.FAILED
    assert "shutdown" in rec_active.message.lower()

    rec_crash = manager2.get("crashed_job")
    assert rec_crash is not None
    assert rec_crash.status == JobStatus.FAILED
    assert "restart" in rec_crash.message.lower()
    assert not exists("tmp/downloads/crashed_job")

    await manager2.shutdown()
    delete(journal_path)
    delete("tmp/test_downloads")
