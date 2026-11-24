from __future__ import annotations
import asyncio
from unittest.mock import patch
import pytest
from src.config import ensure_dir, exists, write_text
from src.helpers import AppError
from src.schema import JobStatus
from src.apps.jobs.helpers.job_journal import JobRecord
from src.apps.jobs.helpers.job_runner import (
    JobRunner,
    _command_matches,
    kill_stale_tree,
    kill_stale_tree_async,
)

def test_command_matches_logic() -> None:
    assert _command_matches(["/usr/bin/ffmpeg", "-i", "a.mp4"], ["ffmpeg", "-i", "a.mp4"])
    assert not _command_matches(["/usr/bin/ffmpeg", "-i", "a.mp4"], ["ffmpeg", "-i", "b.mp4"])
    assert not _command_matches(["yt-dlp"], ["ffmpeg"])
    assert _command_matches([], [])

def test_kill_stale_tree_non_existent_pid() -> None:
    assert not kill_stale_tree(999999, ["ffmpeg"])

@pytest.mark.asyncio
async def test_kill_stale_tree_async_non_existent_pid() -> None:
    res = await kill_stale_tree_async(999999, ["ffmpeg"])
    assert not res

@pytest.mark.asyncio
async def test_kill_stale_tree_successful_mock() -> None:
    with patch("src.apps.jobs.helpers.job_runner.sys_read_bytes", return_value=b"ffmpeg\x00-i\x00test.mp4\x00"):
        with patch("os.getpgid", return_value=12345):
            with patch("os.killpg") as mock_killpg:
                res = await kill_stale_tree_async(12345, ["ffmpeg", "-i", "test.mp4"])
                assert res
                assert mock_killpg.call_count >= 1

@pytest.mark.asyncio
async def test_job_runner_successful_execution() -> None:
    runner = JobRunner()
    job = JobRecord("run_job_1", "test_svc", "127.0.0.1", user_id="usr_42")

    async def mock_exec(*args, on_progress=None, **kwargs) -> str:
        assert kwargs.get("user_id") == "usr_42"
        if on_progress:
            on_progress(50, "Halfway done")
        return "tmp/downloads/run_job_1/output.mp4"

    res = await runner.run(job, mock_exec)
    assert res == "tmp/downloads/run_job_1/output.mp4"
    assert job.status == JobStatus.COMPLETE
    assert job.progress == 100

@pytest.mark.asyncio
async def test_job_runner_timeout_and_cleanup() -> None:
    runner = JobRunner()
    job = JobRecord("run_job_timeout", "test_svc", "127.0.0.1")
    partial_dir = f"tmp/downloads/{job.job_id}"
    ensure_dir(partial_dir)
    write_text(f"{partial_dir}/temp.part", "incomplete_data")
    assert exists(partial_dir)

    async def slow_exec(*args, **kwargs) -> str:
        await asyncio.sleep(0.5)
        return "out"

    res = await runner.run(job, slow_exec, timeout=0.05)
    assert res is None
    assert job.status == JobStatus.FAILED
    assert "timed out" in str(job.error)
    assert not exists(partial_dir)

@pytest.mark.asyncio
async def test_job_runner_exception_handling_and_cleanup() -> None:
    runner = JobRunner()
    job = JobRecord("run_job_err", "test_svc", "127.0.0.1")
    partial_dir = f"tmp/downloads/{job.job_id}"
    ensure_dir(partial_dir)
    write_text(f"{partial_dir}/temp.part", "incomplete_data")

    async def failing_exec(*args, **kwargs) -> str:
        raise AppError("Corrupted stream input")

    res = await runner.run(job, failing_exec)
    assert res is None
    assert job.status == JobStatus.FAILED
    assert "Corrupted stream input" in str(job.error)
    assert not exists(partial_dir)

@pytest.mark.asyncio
async def test_job_runner_filters_unexpected_kwargs_such_as_resource_permit() -> None:
    runner = JobRunner()
    job = JobRecord("run_job_permit", "time_range", "127.0.0.1", user_id="usr_99")

    async def strict_executor(url: str, on_progress=None, user_id=None) -> str:
        assert user_id == "usr_99"
        return f"processed:{url}"

    res = await runner.run(
        job,
        strict_executor,
        args=("http://example.com/video.mp4",),
        kwargs={"resource_permit": "permit_obj", "unrelated_flag": True},
    )
    assert res == "processed:http://example.com/video.mp4"
    assert job.status == JobStatus.COMPLETE
