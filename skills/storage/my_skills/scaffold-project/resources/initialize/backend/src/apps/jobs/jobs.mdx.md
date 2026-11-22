# jobs.py DOX

> *`src/apps/jobs/` acts as the "Production Factory":*
> *It ingests client requests, maintains order queues (Pending, Running, Done), and enforces priority ordering.*
> *Whenever executing heavy workloads, it requests an active hardware lease (e.g. a 30-second GPU token) from the central resource bank (`src/apps/system/`).*

## Purpose

- Own the `src/apps/jobs` asynchronous workload and job orchestration platform substrate.
- Decouple client request intake, priority queueing, deduplication, execution, and progress streaming from domain-specific business logic.
- Coordinate with the central resource governor (`src/apps/system/` `SystemManager`) to dynamically lease hardware tokens (GPU, CPU threads, memory) on demand without coupling to specific domain operations.
- Provide reliable Server-Sent Events (SSE) streaming progress, distributed Redis pub/sub synchronization, and process-tree lifecycle supervision.
- Keep this module-level DOX profile synchronized with `src/apps/jobs/` implementation files.

## Ownership

- `src/apps/jobs/manager.py` owns the public facade and lifecycle orchestrator (`JobManager`).
- `src/apps/jobs/helpers/` owns the isolated sub-engine worker implementations ("internal machinery").
- `jobs.mdx.md` owns durable notes about responsibilities, runtime contracts, side effects, key concepts, work guidance, and verification.
- **Classes:**
  - `JobManager` (Public Facade / Orchestrator)
    - `async start(self) -> None`
    - `async shutdown(self) -> None`
    - `find_duplicate(self, content_hash: str) -> Optional[JobRecord]`
    - `async submit(self, job_id: str, service_type: str, client_ip: str, executor: Callable[..., Awaitable[str]], *args, ...) -> JobRecord`
    - `get(self, job_id: str) -> Optional[JobRecord]`
    - `active_count(self) -> int`
    - `stream_progress(self, job_id: str) -> AsyncGenerator[str, None]`
    - `get_instance(cls) -> JobManager`
  - `JobControl` (`helpers/job_control.py`)
    - `active_tokens -> int`
    - `acquire_resource_permit(self, workload_type: str, job_id: str, user_tier: UserTier, timeout: float) -> Optional[ResourcePermit]`
    - `acquire_resource_token(self, workload_type: str, job_id: str, user_tier: UserTier, timeout: float) -> Optional[ResourceLease]`
    - `release_resource_token(self, job_id: str) -> None`
    - `reap_expired_tokens(self, ttl: float) -> list[str]`
    - `check_capacity(self, client_ip: str, user_id: Optional[str], tier: Optional[str]) -> None`
    - `record_active_job(self, client_ip: str, content_hash: Optional[str], job_id: str, user_id: Optional[str]) -> None`
    - `register_submission(self, client_ip: str, content_hash: Optional[str], job_id: str, user_id: Optional[str]) -> None`
    - `release_job(self, client_ip: str, content_hash: Optional[str], job_id: Optional[str], user_id: Optional[str]) -> None`
  - `JobRecord` (`helpers/job_journal.py`)
    - Data contract tracking job status (`RECEIVED`, `VALIDATED`, `QUEUED`, `LEASING`, `PROCESSING`, `COMMITTING`, `COMPLETE`, `FAILED`, `TIMEOUT`, `TOMBSTONE`, `PURGED`), progress milestones, output artifacts, error details, and event synchronization.
    - `to_progress(self) -> JobProgress`
    - `update(self, progress: int, message: str, status: Optional[JobStatus], metadata: Optional[dict]) -> None`
    - `complete(self, output_path: str) -> None`
    - `fail(self, error: BaseException | str) -> None`
    - `cancel(self) -> None`
    - `mark_tombstone(self, ttl: float) -> None`
    - `is_tombstone_expired(self) -> bool`
    - `purge(self) -> None`
    - `is_terminal -> bool`
  - `JobResults` (`helpers/job_results.py`)
    - `get(self, job_id: str) -> Optional[JobRecord]`
    - `active_count(self) -> int`
    - `commit_staging(self, job: JobRecord, staging_path: str, final_filename: str) -> str`
    - `record_file(self, job: JobRecord, output_path: str) -> None`
  - `JobRunner` (`helpers/job_runner.py`)
    - `run(self, job: JobRecord, executor: Callable[..., Awaitable[str]], args: tuple, kwargs: Optional[dict], timeout: Optional[float]) -> Optional[str]`
  - `JobSubmission` (`helpers/job_submission.py`)
    - `find_duplicate(self, content_hash: str) -> Optional[JobRecord]`
    - `submit(self, job_id: str, service_type: str, client_ip: str, executor: Callable[..., Awaitable[str]], *args, ...) -> JobRecord`
  - `JobWorker` (`helpers/job_worker.py`)
    - `execute_job(self, job: JobRecord, executor: Callable[..., Awaitable[str]], args: tuple, kwargs: Optional[dict], needs_encode: bool, content_hash: Optional[str], workload_type: Optional[str], timeout: float) -> None`
    - `execute_stage_pipeline(self, job: JobRecord, download_stage: Callable[..., Awaitable[str]], encode_stage: Optional[Callable[[str], Awaitable[str]]], content_hash: Optional[str], timeout: float) -> Optional[str]`
  - `LiveMonitor` (`helpers/live_monitor.py`)
    - `start(self) -> None`
    - `shutdown(self) -> None`
    - `stream_progress(self, job_id: str) -> AsyncGenerator[str, None]`
- **Top-level Functions:**
  - `get_manager() -> JobManager`
  - `compute_canonical_job_hash(service_type: str, target: str, params: Optional[dict]) -> str`
  - `resolve_stream_lane(tier: Optional[str]) -> str`
  - `plan_recovery(records: dict) -> RecoveryPlan`
  - `sanitize_client_error(error: BaseException | str) -> str`
  - `kill_stale_tree(pid: int, expected_cmd: list[str]) -> bool`
  - `kill_stale_tree_async(pid: int, expected_cmd: list[str]) -> Awaitable[bool]`
- **Notable Configurations (from `Settings`):**
  - `Settings.MAX_ACTIVE_JOBS_PER_IP`
  - `Settings.MAX_USER_CONCURRENT_JOBS`
  - `Settings.MAX_QUEUE_DEPTH`
  - `Settings.JOB_MAX_RUNTIME`
  - `Settings.TEMP_FILE_TTL_SECONDS`

## Runtime Contracts

- **Singleton Pattern:** External callers always access `JobManager` via `get_manager()` or `JobManager.get_instance()`.
- **Zero-Trust Resource Leasing:** Compute-heavy workloads (e.g., ffmpeg encoding) must never run on-demand without leasing capacity from `SystemManager` (`src/apps/system/`).
- **Distributed & In-Memory Deduplication:** Requests with matching canonical hashes return existing active `JobRecord` handles without duplicate execution.
- **Process Tree Hygiene & Safety:** Any spawned subprocess must run in an isolated process group and be reaped via `kill_stale_tree` with `/proc/<pid>/cmdline` verification to prevent PID recycling accidents.
- **Strict Error Sanitization:** Raw exceptions and internal tracebacks must pass through `sanitize_client_error()` before persisting to user-facing payloads.
- **Observed Side-Effect Areas:**
  - Subprocess execution (FFmpeg, yt-dlp).
  - Staging and final filesystem artifact creation under `tmp/downloads/` and `data/`.
  - Distributed Redis pub/sub broadcasting (`job:{job_id}:progress`).
  - Hardware/token allocations against `SystemManager`.
- **Imported Dependency Areas:**
  - `src.config` (Settings, setup_logger, path utilities).
  - `src.apps.system` (SystemManager, resource leasing).
  - `src.schema` (JobStatus, JobResponse, JobProgress, system schemas).
  - `src.helpers` (AppError, RateLimitError, get_redis).

## Key Concepts

- **"Production Factory" Substrate:**
  1. Intake: User requests enter via REST API (`JobManager.submit`).
  2. Queue & Dedup: `JobSubmission` verifies IP capacity and in-memory/Redis deduplication hashes.
  3. Lease Acquisition: `JobControl` requests an active hardware token lease from `SystemManager`.
  4. Execution: `JobWorker` and `JobRunner` manage the subprocess lifecycle with timeout guards.
  5. Commit & Stream: `JobResults` commits staged outputs while `LiveMonitor` streams SSE updates.
- **Sub-Engine Isolation ("Internal Machinery"):**
  - All worker components reside strictly in `src/apps/jobs/helpers/` and are private to `src/apps/jobs/`.
  - External modules never import private helpers directly; they only consume `src.apps.jobs.get_manager()` or `JobManager`.
- **Closed-Loop Feedback:** Failed or timed-out jobs trigger circuit breaker feedback and immediately release leased tokens back to `SystemManager`.

## Work Guidance

- Never expose or import `src/apps/jobs/helpers/*` outside of `src/apps/jobs/`.
- Ensure all subprocess invocations inherit process-group supervision and verify cmdlines before termination.
- All temporary files must use `src.config` sandboxed filesystem functions (`ensure_dir`, `write_text`, `delete`).
- Preserve zero-comment and zero-docstring clean code rules inside Python implementations.

## Verification

- Run AST architecture compliance linter:
  ```bash
  human-skills '{"tool_name": "linter", "tool_args": {"scan_path": "src/apps/jobs"}}'
  ```
- Run targeted sub-engine and lifecycle test suites:
  ```bash
  PYTHONPATH=. pytest tests/apps/jobs/ -v --durations=0
  ```
- Related test suites:
  - `tests/apps/jobs/test_job_control.py`
  - `tests/apps/jobs/test_job_journal.py`
  - `tests/apps/jobs/test_job_manager.py`
  - `tests/apps/jobs/test_job_results.py`
  - `tests/apps/jobs/test_job_runner.py`
  - `tests/apps/jobs/test_job_submission.py`
  - `tests/apps/jobs/test_job_worker.py`
  - `tests/apps/jobs/test_live_monitor.py`

## Child DOX Index

- [helpers/job_control.py](helpers/job_control.py)
- [helpers/job_journal.py](helpers/job_journal.py)
- [helpers/job_results.py](helpers/job_results.py)
- [helpers/job_runner.py](helpers/job_runner.py)
- [helpers/job_submission.py](helpers/job_submission.py)
- [helpers/job_worker.py](helpers/job_worker.py)
- [helpers/live_monitor.py](helpers/live_monitor.py)
