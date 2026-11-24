from __future__ import annotations
from unittest.mock import AsyncMock
import pytest
from src.config import delete, ensure_dir, exists, write_text
from src.schema import JobStatus
from src.apps.jobs.helpers.job_journal import JobRecord
from src.apps.jobs.helpers.job_results import JobResults, _calculate_output_size_mb

def test_calculate_output_size_mb_single_file_and_dir() -> None:
    test_dir = "tmp/test_calc"
    ensure_dir(test_dir)
    write_text(f"{test_dir}/file1.txt", "a" * 1024 * 1024)
    write_text(f"{test_dir}/file2.txt", "b" * 1024 * 1024)

    single_size = _calculate_output_size_mb(f"{test_dir}/file1.txt")
    assert single_size >= 1.0

    dir_size = _calculate_output_size_mb(test_dir)
    assert dir_size >= 2.0

    assert _calculate_output_size_mb("tmp/non_existent_file_xyz") == 0.0
    delete(test_dir)

@pytest.mark.asyncio
async def test_job_results_commit_staging() -> None:
    job = JobRecord("res_job_1", "test_svc", "127.0.0.1", user_id="usr_100")
    staging_file = "tmp/staging_sample.mp4"
    write_text(staging_file, "mock_video_bytes")

    results = JobResults({job.job_id: job})
    callback_mock = AsyncMock()
    results.set_completion_callback(callback_mock)

    final_rel = await results.commit_staging(job, staging_file, "final_video.mp4")
    assert final_rel == "tmp/downloads/res_job_1/final_video.mp4"
    assert job.output_path == final_rel
    assert exists(final_rel)
    assert not exists(staging_file)

    meta = job.metadata or {}
    assert "file_size_mb" in meta
    assert "tier" in meta
    assert "expires_at" in meta
    callback_mock.assert_awaited_once()

    delete("tmp/downloads/res_job_1")

@pytest.mark.asyncio
async def test_job_results_record_file_directory_output() -> None:
    job = JobRecord("res_job_dir", "batch_svc", "127.0.0.1")
    output_dir = "tmp/downloads/res_job_dir"
    ensure_dir(output_dir)
    write_text(f"{output_dir}/item1.txt", "data")

    results = JobResults({job.job_id: job})
    await results.record_file(job, output_dir)

    meta = job.metadata or {}
    assert meta.get("file_size_mb") is not None
    assert meta.get("tier") is not None

    delete(output_dir)

def test_job_results_get_and_active_count() -> None:
    job1 = JobRecord("res_job_active", "svc", "127.0.0.1")
    job2 = JobRecord("res_job_done", "svc", "127.0.0.1")
    job2.complete("out")

    registry = {job1.job_id: job1, job2.job_id: job2}
    results = JobResults(registry)

    assert results.get("res_job_active") is job1
    assert results.get("non_existent") is None
    assert results.active_count() == 1

