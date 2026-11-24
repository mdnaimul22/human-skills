from __future__ import annotations
import asyncio
from unittest.mock import MagicMock, patch
import pytest
from src.helpers import AppError
from src.schema import JobStatus
from src.apps.jobs.helpers.job_journal import (
    JobRecord,
    RecoveryPlan,
    _extract_status,
    plan_recovery,
)

def test_extract_status_and_plan_recovery() -> None:
    job_complete = JobRecord("job_c", "svc", "127.0.0.1")
    job_complete.complete("out.mp4")

    records = {
        "job_c": job_complete,
        "job_inf": {"status": "processing"},
        "job_fail": {"status": "failed"},
        "job_timeout": {"status": "timeout"},
        "job_bad": {"invalid": "missing_status"},
        "job_corrupt": {"status": "unknown_state_xyz"},
    }

    plan = plan_recovery(records)
    assert plan.completed == ["job_c"]
    assert plan.in_flight == ["job_inf"]
    assert "job_fail" in plan.failed
    assert "job_timeout" in plan.failed
    assert "job_bad" in plan.corrupt
    assert "job_corrupt" in plan.corrupt

def test_job_record_lifecycle_and_terminal_guard() -> None:
    job = JobRecord("rec_job_1", "svc", "127.0.0.1", user_id="usr_10")
    assert job.status == JobStatus.RECEIVED
    assert job.progress == 0
    assert not job.is_terminal

    job.update(45, "Encoding stream", JobStatus.PROCESSING)
    assert job.status == JobStatus.PROCESSING
    assert job.progress == 45
    assert job.message == "Encoding stream"

    job.complete("tmp/downloads/video.mp4")
    assert job.status == JobStatus.COMPLETE
    assert job.progress == 100
    assert job.is_terminal

    job.update(20, "Should not regress", JobStatus.PROCESSING)
    assert job.status == JobStatus.COMPLETE
    assert job.progress == 100

def test_job_record_fail_with_app_error() -> None:
    job = JobRecord("rec_job_err", "svc", "127.0.0.1")
    err = AppError("Media format unsupported", error_code="UNSUPPORTED_FORMAT")
    job.fail(err)

    assert job.status == JobStatus.FAILED
    assert job.is_terminal
    assert "Media format unsupported" in str(job.error)
    assert job.diagnostic_error is not None
    assert "UNSUPPORTED_FORMAT" in job.diagnostic_error or "AppError" in job.diagnostic_error

def test_job_record_cancel() -> None:
    job = JobRecord("rec_job_cancel", "svc", "127.0.0.1")
    job.cancel()
    assert job.status == JobStatus.FAILED
    assert job._cancelled
    assert "cancelled" in str(job.error)

def test_job_record_tombstone_and_purge() -> None:
    job = JobRecord("rec_job_tomb", "svc", "127.0.0.1")
    job.mark_tombstone(ttl=-5.0)
    assert job.status == JobStatus.TOMBSTONE
    assert job.is_tombstone_expired()

    job.purge()
    assert job.status == JobStatus.PURGED

@pytest.mark.asyncio
async def test_job_record_to_progress_and_signal() -> None:
    job = JobRecord("rec_job_prog", "svc", "127.0.0.1")
    logs = [f"Log line {i}" for i in range(50)]
    job.metadata = {"logs": logs}
    job.complete("tmp/downloads/rec_job_prog/final.mp4")

    prog = job.to_progress()
    assert prog.job_id == "rec_job_prog"
    assert prog.status == JobStatus.COMPLETE
    assert prog.download_url == "/api/v1/tools/download/rec_job_prog"
    meta = prog.metadata or {}
    assert len(meta.get("logs", [])) == 30

    assert job._event.is_set()

def test_job_record_serialization_and_journal_store() -> None:
    from src.config import delete
    from src.apps.jobs.helpers.job_journal import JobJournalStore
    journal_file = "tmp/test_journal_store.json"
    store = JobJournalStore(journal_file)
    job = JobRecord("j_persist_1", "video", "10.0.0.1", user_id="usr_123")
    job.update(25, "Processing stream", JobStatus.PROCESSING, metadata={"tier": "premium"})

    data = job.to_dict()
    assert data["job_id"] == "j_persist_1"
    assert data["status"] == "processing"
    assert data["progress"] == 25
    assert data["user_id"] == "usr_123"

    job_restored = JobRecord.from_dict(data)
    assert job_restored.job_id == job.job_id
    assert job_restored.status == JobStatus.PROCESSING
    assert job_restored.progress == 25
    assert job_restored.user_id == "usr_123"

    store.save_record_sync(data)
    loaded = store.load_records()
    assert "j_persist_1" in loaded
    assert loaded["j_persist_1"]["progress"] == 25

    store.remove_record("j_persist_1")
    assert "j_persist_1" not in store.load_records()
    delete(journal_file)

def test_job_record_tier_preservation() -> None:
    job = JobRecord("j_tier_1", "video", "10.0.0.1", user_id="usr_tier", tier="premium")
    assert job.tier == "premium"
    assert job.metadata is not None
    assert job.metadata.get("tier") == "premium"

    job.update(30, "Downloading", JobStatus.PROCESSING, metadata={"progress_pct": 30})
    assert job.tier == "premium"
    assert job.metadata.get("tier") == "premium"
    assert job.metadata.get("progress_pct") == 30

    data = job.to_dict()
    assert data["tier"] == "premium"

    restored = JobRecord.from_dict(data)
    assert restored.tier == "premium"
    assert restored.metadata is not None
    assert restored.metadata.get("tier") == "premium"

