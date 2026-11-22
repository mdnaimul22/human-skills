from __future__ import annotations
import os
from typing import Awaitable, Callable, Optional
from src.config import Settings, ensure_dir, get_abs_path, get_size, is_dir, is_file, list_files, setup_logger
from src.helpers import get_now_utc, resolve_ttl
from .job_journal import JobRecord

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="jobs.results")

OnCompleteCallback = Callable[[JobRecord, str, float], Awaitable[None]]

def _calculate_output_size_mb(output_path: str) -> float:
    if is_dir(output_path):
        size_bytes = sum(entry.stat().st_size for entry in list_files(output_path, "**/*") if is_file(str(entry)))
        return round(size_bytes / (1024 * 1024), 2)
    if is_file(output_path):
        return round(get_size(output_path) / (1024 * 1024), 2)
    return 0.0

async def _enrich_media_metadata(output_path: str, meta: dict) -> None:
    expected_format = meta.get("format")
    try:
        from src.core.ffmpeg_manager import probe_media_format, verify_media_format
        probe = await probe_media_format(output_path)
        meta["media_probe"] = probe.model_dump()
        meta["duration"] = probe.duration
        if expected_format:
            await verify_media_format(output_path, str(expected_format))
    except Exception as e:
        logger.debug(f"Media metadata probe bypassed for {output_path}: {e}")

class JobResults:
    def __init__(self, jobs_registry: dict[str, JobRecord]) -> None:
        self._jobs = jobs_registry
        self.on_complete_callback: Optional[OnCompleteCallback] = None

    def set_completion_callback(self, callback: OnCompleteCallback) -> None:
        self.on_complete_callback = callback

    def get(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def active_count(self) -> int:
        return sum(1 for j in self._jobs.values() if not j.is_terminal)

    async def commit_staging(
        self,
        job: JobRecord,
        staging_path: str,
        final_filename: str,
    ) -> str:
        target_dir = f"tmp/downloads/{job.job_id}"
        ensure_dir(target_dir)
        final_rel = f"{target_dir}/{final_filename}"
        os.replace(get_abs_path(staging_path), get_abs_path(final_rel))
        job.output_path = final_rel
        await self.record_file(job, final_rel)
        return final_rel

    async def record_file(self, job: JobRecord, output_path: str) -> None:
        try:
            tier, ttl = resolve_ttl(job.user_id, None)
            expires_at = get_now_utc() + ttl
            file_size_mb = _calculate_output_size_mb(output_path)

            meta = job.metadata or {}
            if is_file(output_path):
                await _enrich_media_metadata(output_path, meta)

            meta["expires_at"] = expires_at.isoformat()
            meta["tier"] = tier
            meta["file_size_mb"] = file_size_mb
            job.metadata = meta
            job._update_count += 1
            job._signal()

            logger.info(f"[{job.job_id}] db.write file_record size_mb={file_size_mb} tier={tier} ttl={ttl}s")

            if self.on_complete_callback:
                try:
                    await self.on_complete_callback(job, output_path, file_size_mb)
                except Exception as cb_err:
                    logger.error(f"[{job.job_id}] Persistence callback error: {cb_err}", exc_info=True)
        except Exception as e:
            job.fail(e)
            logger.error(f"[{job.job_id}] record_file failed: {e}", exc_info=True)
            raise e
