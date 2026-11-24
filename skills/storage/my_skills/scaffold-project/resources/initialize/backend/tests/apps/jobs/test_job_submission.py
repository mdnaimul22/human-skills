from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.helpers import RateLimitError
from src.schema import JobStatus
from src.apps.system import SystemManager
from src.apps.jobs.helpers.job_control import JobControl
from src.apps.jobs.helpers.job_journal import JobRecord
from src.apps.jobs.helpers.job_worker import JobWorker
from src.apps.jobs.helpers.job_submission import (
    JobSubmission,
    compute_canonical_job_hash,
    resolve_stream_lane,
)

@pytest.fixture(autouse=True)
def clean_system() -> None:
    SystemManager.reset_instance()
    yield
    SystemManager.reset_instance()

@pytest.fixture(autouse=True)
def mock_redis():
    with patch("src.apps.jobs.helpers.job_submission.get_redis") as mock_get:
        redis_inst = MagicMock()
        redis_inst.is_available = False
        mock_get.return_value = redis_inst
        yield redis_inst

def _create_submission() -> tuple[JobSubmission, dict[str, JobRecord], JobControl, MagicMock]:
    jobs: dict[str, JobRecord] = {}
    control = JobControl(SystemManager.get_instance())
    worker = MagicMock(spec=JobWorker)
    worker.execute_job = AsyncMock()
    sub = JobSubmission(jobs, control, worker)
    return sub, jobs, control, worker

def test_canonical_job_hash_normalization() -> None:
    h1 = compute_canonical_job_hash(
        "download", "https://WWW.Example.Com/item?id=123&b=2&a=1", {"format": "json"}
    )
    h2 = compute_canonical_job_hash(
        "download", "https://example.com/item?a=1&b=2&id=123", {"format": "json"}
    )
    assert h1 == h2

    h3 = compute_canonical_job_hash("process", "raw_non_url_target", None)
    assert len(h3) == 64

def test_resolve_stream_lane() -> None:
    assert resolve_stream_lane("Premium") == "jobs:stream:premium"
    assert resolve_stream_lane("registered") == "jobs:stream:registered"
    assert resolve_stream_lane(None) == "jobs:stream:guest"
    assert resolve_stream_lane("unknown") == "jobs:stream:guest"

@pytest.mark.asyncio
async def test_job_submission_normal_lifecycle() -> None:
    sub, jobs, control, worker = _create_submission()

    async def mock_exec(*args, **kwargs) -> str:
        return "tmp/out.mp4"

    job = await sub.submit(
        job_id="sub_job_1",
        service_type="download",
        client_ip="192.168.1.10",
        executor=mock_exec,
        workload_type="custom_workload",
        user_id="usr_1",
        url="https://example.com/item?id=abc",
    )
    assert job.job_id == "sub_job_1"
    assert job.status == JobStatus.QUEUED
    assert "sub_job_1" in jobs
    assert control.ip_active["192.168.1.10"] == 1
    assert control.user_active["usr_1"] == 1
    worker.execute_job.assert_called_once()
    assert worker.execute_job.call_args.kwargs["workload_type"] == "custom_workload"

@pytest.mark.asyncio
async def test_job_submission_deduplication_in_memory() -> None:
    sub, jobs, control, worker = _create_submission()

    async def dummy_exec(*args, **kwargs) -> str:
        return "out"

    job1 = await sub.submit(
        job_id="sub_job_orig",
        service_type="download",
        client_ip="127.0.0.1",
        executor=dummy_exec,
        content_hash="content_hash_123",
    )
    assert job1.job_id == "sub_job_orig"

    job2 = await sub.submit(
        job_id="sub_job_dup",
        service_type="download",
        client_ip="127.0.0.1",
        executor=dummy_exec,
        content_hash="content_hash_123",
    )
    assert job2.job_id == "sub_job_orig"
    assert len(jobs) == 1
    assert worker.execute_job.call_count == 1

@pytest.mark.asyncio
async def test_job_submission_capacity_rejection_leaves_state_clean() -> None:
    sub, jobs, control, worker = _create_submission()
    control.ip_active["10.0.0.5"] = 50

    async def dummy_exec(*args, **kwargs) -> str:
        return "out"

    with pytest.raises(RateLimitError):
        await sub.submit(
            job_id="sub_job_rejected",
            service_type="download",
            client_ip="10.0.0.5",
            executor=dummy_exec,
            content_hash="rejected_hash",
        )

    assert "sub_job_rejected" not in jobs
    assert "rejected_hash" not in control.dedup_index
    assert worker.execute_job.call_count == 0

@pytest.mark.asyncio
async def test_job_submission_redis_dedup_hit(mock_redis) -> None:
    sub, jobs, control, worker = _create_submission()
    mock_redis.is_available = True
    mock_redis.acquire_dedup = AsyncMock(return_value=(False, "redis_owner_job"))
    mock_redis.get_state = AsyncMock(return_value='{"status": "processing", "progress": 42}')

    async def dummy_exec(*args, **kwargs) -> str:
        return "out"

    job = await sub.submit(
        job_id="sub_job_redis_follower",
        service_type="download",
        client_ip="127.0.0.1",
        executor=dummy_exec,
        content_hash="shared_redis_hash",
    )

    assert job.job_id == "redis_owner_job"
    assert job.status == JobStatus.PROCESSING
    assert job.progress == 42
    assert worker.execute_job.call_count == 0
