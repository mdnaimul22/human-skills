from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol, Union
from src.config import Settings, exists, read_json, setup_logger, write_json
from src.schema import JobProgress, JobStatus
from src.helpers import AppError, get_redis, sanitize_client_error, sanitize_client_path

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="jobs.journal")

@dataclass
class RecoveryPlan:
    completed: list[str] = field(default_factory=list)
    in_flight: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    corrupt: list[str] = field(default_factory=list)

class StatusHolder(Protocol):
    status: JobStatus | str

RecordSource = Union[dict[str, str], StatusHolder]

def _extract_status(rec: RecordSource) -> Optional[str]:
    match rec:
        case dict() as d:
            val = d.get("status")
            return str(val) if val else None
        case JobRecord() as job:
            return job.status.value
        case StatusHolder() as holder:
            raw = holder.status
            match raw:
                case JobStatus() as st:
                    return st.value
                case str() as s:
                    return s
                case _:
                    return str(raw) if raw else None
        case _:
            return None

def _classify_record(jid: str, rec: RecordSource, plan: RecoveryPlan) -> None:
    status_val = _extract_status(rec)
    if not status_val:
        plan.corrupt.append(jid)
        return
    if status_val == "complete":
        plan.completed.append(jid)
        return
    if status_val in ("failed", "timeout", "tombstone", "purged"):
        plan.failed.append(jid)
        return
    if status_val in ("received", "validated", "queued", "leasing", "processing", "draining", "committing"):
        plan.in_flight.append(jid)
        return
    plan.corrupt.append(jid)

def plan_recovery(records: dict) -> RecoveryPlan:
    plan = RecoveryPlan()
    for jid, rec in records.items():
        _classify_record(str(jid), rec, plan)
    return plan

class JobJournalStore:
    def __init__(self, journal_path: str = "data/jobs_journal.json") -> None:
        self.journal_path = journal_path
        self._dirty = False
        self._cache: dict[str, dict] = {}
        self._loaded = False

    def load_records(self) -> dict[str, dict]:
        if not exists(self.journal_path):
            return {}
        try:
            raw = read_json(self.journal_path)
            match raw:
                case dict() as d:
                    self._cache = dict(d)
                    self._loaded = True
                    return dict(d)
                case _:
                    return {}
        except Exception as e:
            logger.warning(f"Failed to read job journal '{self.journal_path}': {e}")
        return {}

    def save_record_sync(self, record_dict: dict) -> None:
        jid = str(record_dict.get("job_id", ""))
        if not jid:
            return
        self._cache[jid] = record_dict
        self._dirty = True
        self.flush()

    def remove_record(self, job_id: str) -> None:
        if job_id in self._cache:
            self._cache.pop(job_id, None)
            self._dirty = True
            self.flush()

    def flush(self) -> None:
        if not self._dirty:
            return
        try:
            if len(self._cache) > 500:
                sorted_keys = sorted(
                    self._cache.keys(),
                    key=lambda k: float(self._cache[k].get("saved_at", 0) or 0),
                )
                for k in sorted_keys[: len(self._cache) - 500]:
                    if self._cache[k].get("status") in ("complete", "failed", "tombstone", "purged"):
                        self._cache.pop(k, None)
            write_json(self.journal_path, self._cache)
            self._dirty = False
        except Exception as e:
            logger.error(f"Failed to flush job journal: {e}")

class JobRecord:
    _journal_store: Optional[JobJournalStore] = None
    __slots__ = (
        "job_id",
        "service_type",
        "status",
        "progress",
        "message",
        "created_at",
        "started_at",
        "completed_at",
        "output_path",
        "error",
        "diagnostic_error",
        "client_ip",
        "_event",
        "_update_count",
        "_cancelled",
        "_loop",
        "user_id",
        "_tier",
        "metadata",
        "tombstone_until",
        "generation_id",
    )

    def __init__(
        self,
        job_id: str,
        service_type: str,
        client_ip: str,
        user_id: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> None:
        self.job_id = job_id
        self.service_type = service_type
        self.status = JobStatus.RECEIVED
        self.progress = 0
        self.message = "Job received"
        self.created_at = time.monotonic()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.output_path: Optional[str] = None
        self.error: Optional[str] = None
        self.diagnostic_error: Optional[str] = None
        self.client_ip = client_ip
        self.user_id = user_id
        self._tier: Optional[str] = tier.lower().strip() if tier else None
        self.metadata: Optional[dict] = {"tier": self._tier} if self._tier else None
        self.tombstone_until: Optional[float] = None
        self.generation_id: int = 0
        self._event = asyncio.Event()
        self._update_count = 0
        self._cancelled = False
        try:
            self._loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    @property
    def tier(self) -> Optional[str]:
        if self._tier is not None:
            return self._tier
        raw = self.metadata.get("tier") if self.metadata else None
        return str(raw).lower().strip() if raw else None

    @tier.setter
    def tier(self, value: Optional[str]) -> None:
        self._tier = value.lower().strip() if value else None
        if self._tier is not None:
            if self.metadata is None:
                self.metadata = {}
            self.metadata["tier"] = self._tier

    def update(
        self,
        progress: int,
        message: str,
        status: Optional[JobStatus] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        if self.is_terminal:
            return
        self.progress = max(self.progress, min(progress, 99))
        self.message = message
        if status:
            self.status = status
        if metadata is not None:
            if self.metadata is None:
                self.metadata = {}
            self.metadata.update(metadata)
            if self._tier is not None and "tier" not in self.metadata:
                self.metadata["tier"] = self._tier
        self._update_count += 1
        self._signal()

    def complete(self, output_path: str) -> None:
        if self._cancelled or self.is_terminal:
            return
        self.status = JobStatus.COMPLETE
        self.progress = 100
        self.message = "Complete"
        self.output_path = output_path
        self.completed_at = time.monotonic()
        self._update_count += 1
        self._signal()

    def fail(self, error: BaseException | str) -> None:
        if self.is_terminal:
            return
        sanitized = sanitize_client_error(error)
        match error:
            case AppError() as app_err:
                raw_error = f"{app_err.__class__.__name__}: {app_err}"
                err_code = app_err.error_code
                err_type = app_err.__class__.__name__
                classification_val = app_err.classification.value
            case BaseException() as base_err:
                raw_error = f"{base_err.__class__.__name__}: {base_err}"
                err_code = "JOB_FAILED"
                err_type = base_err.__class__.__name__
                classification_val = "system_error"
            case _:
                raw_error = str(error)
                err_code = "JOB_FAILED"
                err_type = "JobError"
                classification_val = "system_error"

        clean_raw = sanitize_client_path(raw_error)
        self.diagnostic_error = clean_raw
        self.status = JobStatus.FAILED
        self.message = sanitized
        self.error = sanitized
        self.completed_at = time.monotonic()
        self._update_count += 1
        logger.error(
            f"Job {self.job_id} failed: {sanitized}",
            extra={
                "job_id": self.job_id,
                "error_code": err_code,
                "error_type": err_type,
                "classification": classification_val,
                "diagnostic_error": clean_raw,
            },
        )
        self._signal()

    def cancel(self) -> None:
        self._cancelled = True
        self.status = JobStatus.FAILED
        self.message = "Job cancelled by user"
        self.error = "Job cancelled by user"
        self.completed_at = time.monotonic()
        self._update_count += 1
        self._signal()

    def mark_tombstone(self, ttl: float = 60.0) -> None:
        self.status = JobStatus.TOMBSTONE
        self.tombstone_until = time.time() + ttl
        self._update_count += 1
        self._signal()

    def is_tombstone_expired(self) -> bool:
        if self.status != JobStatus.TOMBSTONE or self.tombstone_until is None:
            return False
        return time.time() > self.tombstone_until

    def purge(self) -> None:
        self.status = JobStatus.PURGED
        self._update_count += 1
        self._signal()

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            JobStatus.COMPLETE,
            JobStatus.FAILED,
            JobStatus.TIMEOUT,
            JobStatus.TOMBSTONE,
            JobStatus.PURGED,
        )

    def _signal(self) -> None:
        current_loop = None
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and self._loop and current_loop is self._loop:
            self._event.set()
        elif self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._event.set)
        else:
            self._event.set()

        redis = get_redis()
        if redis.is_available:
            loop = current_loop or self._loop
            if loop and loop.is_running():
                payload = self.to_progress().model_dump_json()
                loop.create_task(redis.publish(f"job:progress:{self.job_id}", payload))
                loop.create_task(redis.set_state(self.job_id, payload, ex=3600))

        if JobRecord._journal_store is not None:
            try:
                JobRecord._journal_store.save_record_sync(self.to_dict())
            except Exception as j_err:
                logger.debug(f"Journal sync failed: {j_err}")

    def to_dict(self) -> dict[str, str | int | float | dict | None]:
        safe_meta: dict = {}
        match self.metadata:
            case dict() as meta_dict:
                for k, v in meta_dict.items():
                    if k == "resource_permit":
                        continue
                    match v:
                        case str() | int() | float() | bool() | list() | dict() | None:
                            safe_meta[k] = v
                        case _:
                            safe_meta[k] = str(v)
            case _:
                pass
        return {
            "job_id": self.job_id,
            "service_type": self.service_type,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "client_ip": self.client_ip,
            "user_id": self.user_id,
            "tier": self.tier,
            "output_path": self.output_path,
            "error": self.error,
            "diagnostic_error": self.diagnostic_error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": safe_meta or None,
            "tombstone_until": self.tombstone_until,
            "generation_id": self.generation_id,
            "saved_at": time.time(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int | float | dict | None]) -> JobRecord:
        raw_meta = data.get("metadata")
        tier_raw = data.get("tier")
        tier_val = str(tier_raw) if tier_raw else ""
        if not tier_val:
            match raw_meta:
                case dict() as m:
                    tier_val = str(m.get("tier", ""))
                case _:
                    tier_val = ""
        job = cls(
            job_id=str(data.get("job_id", "")),
            service_type=str(data.get("service_type", "unknown")),
            client_ip=str(data.get("client_ip", "127.0.0.1")),
            user_id=str(data["user_id"]) if data.get("user_id") else None,
            tier=tier_val or None,
        )
        status_str = str(data.get("status", "received"))
        try:
            job.status = JobStatus(status_str)
        except ValueError:
            job.status = JobStatus.FAILED
        job.progress = int(data.get("progress", 0))
        job.message = str(data.get("message", ""))
        job.output_path = str(data["output_path"]) if data.get("output_path") else None
        job.error = str(data["error"]) if data.get("error") else None
        job.diagnostic_error = str(data["diagnostic_error"]) if data.get("diagnostic_error") else None
        match raw_meta:
            case dict() as meta_dict:
                job.metadata = dict(meta_dict)
                if job.tier and "tier" not in job.metadata:
                    job.metadata["tier"] = job.tier
            case _:
                job.metadata = {"tier": job.tier} if job.tier else None
        job.tombstone_until = float(data["tombstone_until"]) if data.get("tombstone_until") else None
        job.generation_id = int(data.get("generation_id", 0))
        return job

    def to_progress(self) -> JobProgress:
        dl_url = f"/api/v1/tools/download/{self.job_id}" if self.status == JobStatus.COMPLETE else None
        safe_meta = sanitize_client_path(self.metadata) if self.metadata else None
        if safe_meta and "logs" in safe_meta:
            match safe_meta["logs"]:
                case list() as log_items if len(log_items) > 30:
                    safe_meta["logs"] = log_items[-30:]
                case _:
                    pass
        return JobProgress(
            job_id=self.job_id,
            status=self.status,
            progress=self.progress,
            message=sanitize_client_path(self.message),
            download_url=dl_url,
            error=sanitize_client_path(self.error),
            metadata=safe_meta,
            tombstone_until=self.tombstone_until,
            generation_id=self.generation_id,
        )
