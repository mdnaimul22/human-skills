from __future__ import annotations
from unittest.mock import AsyncMock
import pytest
from src.helpers import AppError
from src.schema import JobStatus
from src.apps.system import LoadLevel, TokenType, WorkloadProfile
from src.apps.system import SystemManager
from src.apps.jobs.helpers.job_control import JobControl
from src.apps.jobs.helpers.job_journal import JobRecord
from src.apps.jobs.helpers.job_results import JobResults
from src.apps.jobs.helpers.job_runner import JobRunner
from src.apps.jobs.helpers.job_worker import JobWorker, _append_log, _extract_active_paths, active_input_paths

@pytest.fixture(autouse=True)
def clean_system() -> None:
    SystemManager.reset_instance()
    yield
    SystemManager.reset_instance()

def _create_worker() -> tuple[JobWorker, JobControl, JobResults]:
    control = JobControl(SystemManager.get_instance())
    runner = JobRunner()
    results = JobResults({})
    results.record_file = AsyncMock()
    worker = JobWorker(control, runner, results)
    return worker, control, results

@pytest.mark.asyncio
async def test_job_worker_execute_job_success() -> None:
    worker, control, results = _create_worker()
    job = JobRecord("job_wk_1", "download_service", "127.0.0.1")

    async def mock_exec(*args, **kwargs) -> str:
        assert control.active_tokens == 1
        return "tmp/downloads/sample.mp4"

    await worker.execute_job(job, mock_exec, workload_type="download")
    assert job.status == JobStatus.COMPLETE
    assert job.output_path == "tmp/downloads/sample.mp4"
    assert control.active_tokens == 0
    results.record_file.assert_awaited_once_with(job, "tmp/downloads/sample.mp4")

@pytest.mark.asyncio
async def test_job_worker_execute_job_encode_workload() -> None:
    worker, control, results = _create_worker()
    job = JobRecord("job_wk_2", "encode_service", "127.0.0.1")

    async def mock_exec(*args, **kwargs) -> str:
        assert control.active_tokens == 1
        return "tmp/downloads/encoded.mp4"

    await worker.execute_job(job, mock_exec, needs_encode=True)
    assert job.status == JobStatus.COMPLETE
    assert job.output_path == "tmp/downloads/encoded.mp4"
    assert control.active_tokens == 0

@pytest.mark.asyncio
async def test_job_worker_execute_job_capacity_exhausted() -> None:
    sys_mgr = SystemManager.get_instance()
    sys_mgr.register_workload(
        WorkloadProfile(
            name="zero_capacity_workload",
            token_type=TokenType.NETWORK,
            base_permits=0,
            degradation_matrix={
                LoadLevel.NORMAL: 0.0,
                LoadLevel.ELEVATED: 0.0,
                LoadLevel.CRITICAL: 0.0,
                LoadLevel.EMERGENCY: 0.0,
            },
        )
    )
    worker, control, _ = _create_worker()
    job = JobRecord("job_wk_3", "busy_service", "127.0.0.1")

    async def dummy_exec() -> str:
        return "dummy"

    await worker.execute_job(job, dummy_exec, workload_type="zero_capacity_workload", timeout=0.05)
    assert job.status == JobStatus.FAILED
    assert "capacity busy" in str(job.error)

@pytest.mark.asyncio
async def test_job_worker_stage_pipeline_lifecycle() -> None:
    worker, control, results = _create_worker()
    job = JobRecord("job_wk_4", "pipeline_service", "127.0.0.1")

    async def download_fn(*args, **kwargs) -> str:
        assert control.active_tokens == 1
        return "tmp/raw.mp4"

    async def encode_fn(*args, **kwargs) -> str:
        assert args[0] == "tmp/raw.mp4"
        assert control.active_tokens == 1
        return "tmp/final.mp4"

    final_path = await worker.execute_stage_pipeline(job, download_fn, encode_fn)
    assert final_path == "tmp/final.mp4"
    assert job.status == JobStatus.COMPLETE
    assert control.active_tokens == 0
    results.record_file.assert_awaited_once_with(job, "tmp/final.mp4")

@pytest.mark.asyncio
async def test_job_worker_stage_pipeline_failure_in_first_stage() -> None:
    worker, control, results = _create_worker()
    job = JobRecord("job_wk_5", "failing_service", "127.0.0.1")

    async def failing_download(*args, **kwargs) -> str:
        raise AppError("Download connection dropped")

    final_path = await worker.execute_stage_pipeline(job, failing_download)
    assert final_path is None
    assert job.status == JobStatus.FAILED
    assert control.active_tokens == 0

def test_job_worker_log_and_path_helpers() -> None:
    job = JobRecord("job_wk_6", "test_service", "127.0.0.1")
    _append_log(job, "Initial log line")
    meta = job.metadata or {}
    assert "Initial log line" in meta.get("logs", [])

    job.metadata["input_path"] = "tmp/input.mp4"
    job.output_path = "tmp/out.mp4"
    paths: set[str] = set()
    _extract_active_paths(job, paths)
    assert "tmp/input.mp4" in paths
    assert "tmp/out.mp4" in paths

    all_paths = active_input_paths({"job_wk_6": job})
    assert "tmp/input.mp4" in all_paths

@pytest.mark.asyncio
async def test_job_worker_tier_propagation() -> None:
    from src.apps.system import UserTier
    worker, control, results = _create_worker()
    job = JobRecord("job_wk_tier", "pipeline_service", "127.0.0.1", tier="premium")

    observed_permits = []
    async def mock_exec(*args, **kwargs) -> str:
        permit = kwargs.get("resource_permit")
        if permit:
            observed_permits.append(permit)
        return "tmp/done.mp4"

    await worker.execute_job(job, mock_exec, workload_type="download")
    assert len(observed_permits) == 1
    assert observed_permits[0].user_tier == UserTier.PREMIUM
