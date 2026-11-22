from __future__ import annotations
from typing import AsyncGenerator, Awaitable, Callable, Optional
from src.config import Settings, delete, ensure_dir, exists, setup_logger
from src.schema import JobStatus
from src.apps.system import SystemManager, get_system_manager
from .helpers import (
    JobControl,
    JobJournalStore,
    JobRecord,
    JobResults,
    JobRunner,
    JobSubmission,
    JobWorker,
    LiveMonitor,
    plan_recovery,
    sanitize_client_error,
)

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="jobs.manager")

class JobManager:
    _singleton: Optional[JobManager] = None

    def __init__(
        self,
        system_manager: Optional[SystemManager] = None,
        journal_path: str = "data/jobs_journal.json",
    ) -> None:
        self._jobs: dict[str, JobRecord] = {}
        sm = system_manager or get_system_manager()
        self.control = JobControl(sm)
        self.runner = JobRunner()
        self.results = JobResults(self._jobs)
        self.worker = JobWorker(self.control, self.runner, self.results)
        self.submission = JobSubmission(self._jobs, self.control, self.worker)
        self.monitor = LiveMonitor(self._jobs, self.control)
        self.journal = JobJournalStore(journal_path)
        JobRecord._journal_store = self.journal

    def _recover_completed_job(self, jid: str, raw_data: dict) -> bool:
        job = JobRecord.from_dict(raw_data)
        if job.output_path and exists(job.output_path):
            self._jobs[jid] = job
            return True
        job.status = JobStatus.PURGED
        self._jobs[jid] = job
        self.journal.save_record_sync(job.to_dict())
        return False

    def _recover_in_flight_job(self, jid: str, raw_data: dict) -> None:
        job = JobRecord.from_dict(raw_data)
        job.status = JobStatus.FAILED
        job.progress = 100
        job.message = "Job interrupted by server restart. Please retry."
        job.error = "ServerRestartInterruption: Execution was interrupted by backend restart."
        job.diagnostic_error = "Server restarted while job was in-flight."
        self._jobs[jid] = job
        self.journal.save_record_sync(job.to_dict())
        job_dir = f"tmp/downloads/{jid}"
        if exists(job_dir):
            try:
                delete(job_dir)
            except OSError as del_err:
                logger.debug(f"Cleanup of interrupted directory {job_dir} failed: {del_err}")

    async def recover_persisted_jobs(self) -> None:
        records = self.journal.load_records()
        if not records:
            return
        plan = plan_recovery(records)
        recovered_count = 0
        for jid in plan.completed:
            raw = records.get(jid)
            if raw and self._recover_completed_job(jid, raw):
                recovered_count += 1
        for jid in plan.in_flight:
            raw = records.get(jid)
            if raw:
                self._recover_in_flight_job(jid, raw)
        for jid in plan.failed:
            raw = records.get(jid)
            if raw:
                self._jobs[jid] = JobRecord.from_dict(raw)
        logger.info(
            f"jobs.recovered completed={recovered_count} in_flight_interrupted={len(plan.in_flight)} "
            f"failed={len(plan.failed)} total_loaded={len(self._jobs)}"
        )

    async def start(self) -> None:
        ensure_dir("tmp/downloads")
        await self.recover_persisted_jobs()
        self.monitor.start()
        logger.info("JobManager started")

    async def shutdown(self) -> None:
        for job in list(self._jobs.values()):
            if not job.is_terminal:
                job.fail("ServerShutdown: Job interrupted by server shutdown.")
        self.journal.flush()
        await self.monitor.shutdown()
        logger.info("JobManager shutdown")

    def find_duplicate(self, content_hash: str) -> Optional[JobRecord]:
        return self.submission.find_duplicate(content_hash)

    async def submit(
        self,
        job_id: str,
        service_type: str,
        client_ip: str,
        executor: Callable[..., Awaitable[str]],
        *args,
        needs_encode: bool = False,
        workload_type: Optional[str] = None,
        user_id: Optional[str] = None,
        content_hash: Optional[str] = None,
        url: Optional[str] = None,
        params: Optional[dict] = None,
        tier: Optional[str] = None,
        timeout: float = 30.0,
        **kwargs,
    ) -> JobRecord:
        return await self.submission.submit(
            job_id,
            service_type,
            client_ip,
            executor,
            *args,
            needs_encode=needs_encode,
            workload_type=workload_type,
            user_id=user_id,
            content_hash=content_hash,
            url=url,
            params=params,
            tier=tier,
            timeout=timeout,
            **kwargs,
        )

    def get(self, job_id: str) -> Optional[JobRecord]:
        return self.results.get(job_id)

    def active_count(self) -> int:
        return self.results.active_count()

    def stream_progress(self, job_id: str) -> AsyncGenerator[str, None]:
        return self.monitor.stream_progress(job_id)

    @classmethod
    def get_instance(cls) -> JobManager:
        if cls._singleton is None:
            cls._singleton = cls()
        return cls._singleton

    @classmethod
    def reset_instance(cls) -> None:
        cls._singleton = None
        JobRecord._journal_store = None

def get_manager() -> JobManager:
    return JobManager.get_instance()

__all__ = [
    "JobManager",
    "JobRecord",
    "get_manager",
    "sanitize_client_error",
]
