from __future__ import annotations
import asyncio
from typing import Awaitable, Callable, Optional
from src.config import Settings, job_context, setup_logger, set_telemetry
from src.config.logger import request_id_ctx
from src.helpers import AppError, sanitize_client_path
from src.schema import JobStatus
from src.apps.system import ResourcePermit, SystemManager, UserTier
from .job_control import JobControl
from .job_journal import JobRecord
from .job_results import JobResults
from .job_runner import JobRunner

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="jobs.worker")

def _append_log(job: JobRecord, text: str) -> None:
    clean_text = sanitize_client_path(text)
    meta = job.metadata or {}
    logs = meta.setdefault("logs", [])
    logs.append(clean_text)
    if len(logs) > 30:
        del logs[:-30]
    job.metadata = meta
    job._update_count += 1
    job._signal()

def _extract_active_paths(job: JobRecord, paths: set[str]) -> None:
    if not job.is_terminal:
        if job.metadata and "input_path" in job.metadata:
            paths.add(job.metadata["input_path"])
        if job.output_path:
            paths.add(job.output_path)

def active_input_paths(jobs: dict[str, JobRecord]) -> set[str]:
    paths: set[str] = set()
    for job in jobs.values():
        _extract_active_paths(job, paths)
    return paths

def _init_job_telemetry(job: JobRecord) -> None:
    request_id_ctx.set(job.job_id)
    with job_context(job.job_id):
        set_telemetry(
            request_id=job.job_id,
            job_id=job.job_id,
            user_id=str(job.user_id) if job.user_id else None,
            service=job.service_type,
            client_ip=job.client_ip,
            endpoint=f"/api/v1/tools/{job.service_type.replace('_', '-')}",
        )
        logger.info(f"{{started}}-{job.job_id} ({job.service_type})")

def _resolve_user_tier(job: JobRecord) -> UserTier:
    raw_tier = job.tier or (job.metadata.get("tier") if job.metadata else None) or UserTier.GUEST
    try:
        return UserTier(str(raw_tier).lower())
    except ValueError:
        return UserTier.GUEST

def _handle_execution_anomaly(sys_mgr: SystemManager, permit: Optional[ResourcePermit], err: Exception) -> None:
    if permit is not None and permit.gpu_enabled:
        err_lower = str(err).lower()
        if any(tok in err_lower for tok in ("nvenc", "cuda", "gpu", "libcuda", "nvcuda", "hwaccel")):
            sys_mgr.notify_hardware_anomaly(permit.preferred_encoder, str(err)[:200])

class JobWorker:
    def __init__(
        self,
        control: JobControl,
        runner: JobRunner,
        results: JobResults,
    ) -> None:
        self.control = control
        self.runner = runner
        self.results = results

    async def _commit_job_success(self, job: JobRecord, permit: ResourcePermit, output: str) -> None:
        if permit.gpu_enabled:
            self.control.system_manager.record_encoder_success(permit.preferred_encoder)
        job.update(99, "Committing artifacts", JobStatus.COMMITTING)
        await self.results.record_file(job, output)
        job.complete(output)

    async def execute_job(
        self,
        job: JobRecord,
        executor: Callable[..., Awaitable[str]],
        args: tuple = (),
        kwargs: Optional[dict] = None,
        needs_encode: bool = False,
        content_hash: Optional[str] = None,
        workload_type: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        effective_workload = workload_type or ("encode" if needs_encode else "download")
        _init_job_telemetry(job)
        token_acquired = False
        permit_ref: Optional[ResourcePermit] = None
        user_tier = _resolve_user_tier(job)
        try:
            async with self.control.global_sem:
                job.update(0, f"Leasing resources ({effective_workload})", JobStatus.LEASING)
                permit = await self.control.acquire_resource_permit(
                    workload_type=effective_workload,
                    job_id=job.job_id,
                    user_tier=user_tier,
                    timeout=timeout,
                )
                if not permit:
                    job.fail(AppError(f"Resource {effective_workload} capacity busy. Please retry.", status_code=503))
                    return
                permit_ref = permit
                token_acquired = True
                if job.metadata is None:
                    job.metadata = {}
                job.metadata["resource_permit"] = permit
                call_kwargs = dict(kwargs) if kwargs else {}
                call_kwargs["resource_permit"] = permit
                output = await self.runner.run(job, executor, args, call_kwargs)
                if output and job.status == JobStatus.COMPLETE:
                    await self._commit_job_success(job, permit, output)
        except Exception as e:
            _handle_execution_anomaly(self.control.system_manager, permit_ref, e)
            if not job.is_terminal:
                job.fail(e)
                logger.error(f"[{job.job_id}] Worker execution failure: {e}", exc_info=True)
        finally:
            if token_acquired:
                await self.control.release_resource_token(job.job_id)
            await self.control.release_job(job.client_ip, content_hash, job.job_id, user_id=job.user_id)

    async def execute_stage_pipeline(
        self,
        job: JobRecord,
        download_stage: Callable[..., Awaitable[str]],
        encode_stage: Optional[Callable[[str], Awaitable[str]]] = None,
        content_hash: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Optional[str]:
        _init_job_telemetry(job)
        active_token: bool = False
        user_tier = _resolve_user_tier(job)
        try:
            async with self.control.global_sem:
                job.update(0, "Leasing network proxy", JobStatus.LEASING)
                dl_lease = await self.control.acquire_resource_token(
                    workload_type="download",
                    job_id=job.job_id,
                    user_tier=user_tier,
                    timeout=timeout,
                )
                if not dl_lease:
                    job.fail(AppError("Resource download capacity busy. Please retry.", status_code=503))
                    return None
                active_token = True
                job.update(5, "Downloading stream", JobStatus.PROCESSING)
                downloaded_path = await self.runner.run(job, download_stage)
                await self.control.release_resource_token(job.job_id)
                active_token = False
                if not downloaded_path or job.status != JobStatus.COMPLETE:
                    return None

                if encode_stage:
                    job.update(50, "Leasing hardware encoder", JobStatus.LEASING)
                    enc_lease = await self.control.acquire_resource_token(
                        workload_type="encode",
                        job_id=job.job_id,
                        user_tier=user_tier,
                        timeout=timeout,
                    )
                    if not enc_lease:
                        job.fail(AppError("Resource encode capacity busy. Please retry.", status_code=503))
                        return None
                    active_token = True
                    job.update(55, "Encoding media", JobStatus.PROCESSING)
                    encoded_path = await self.runner.run(job, encode_stage, (downloaded_path,))
                    await self.control.release_resource_token(job.job_id)
                    active_token = False
                    if not encoded_path or job.status != JobStatus.COMPLETE:
                        return None
                    final_path = encoded_path
                else:
                    final_path = downloaded_path

                job.update(99, "Committing artifacts", JobStatus.COMMITTING)
                await self.results.record_file(job, final_path)
                job.complete(final_path)
                return final_path
        except Exception as e:
            if not job.is_terminal:
                job.fail(e)
                logger.error(f"[{job.job_id}] Pipeline execution failure: {e}", exc_info=True)
            return None
        finally:
            if active_token:
                await self.control.release_resource_token(job.job_id)
            await self.control.release_job(job.client_ip, content_hash, job.job_id, user_id=job.user_id)
