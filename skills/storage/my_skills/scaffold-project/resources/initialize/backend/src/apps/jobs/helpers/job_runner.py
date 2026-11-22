from __future__ import annotations
import asyncio
import inspect
import os
import signal
import time
from typing import Awaitable, Callable, Optional
from src.config import Settings, delete, exists, read_bytes, request_id_ctx, set_telemetry, setup_logger
from src.schema import JobStatus
from src.apps.system.schema.resource import ResourcePermit
from .job_journal import JobRecord

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="jobs.runner")

def _command_matches(actual: list[str], expected: list[str]) -> bool:
    if len(actual) != len(expected):
        return False
    if not actual or not expected:
        return actual == expected
    if actual[0].split("/")[-1] != expected[0].split("/")[-1]:
        return False
    return actual[1:] == expected[1:]

def kill_stale_tree(pid: int, expected_cmd: list[str]) -> bool:
    cmdline_path = f"/proc/{pid}/cmdline"
    try:
        raw = read_bytes(cmdline_path)
        actual = [arg.decode(errors="replace") for arg in raw.split(b"\x00") if arg]
    except (OSError, IOError):
        return False

    if not _command_matches(actual, expected_cmd):
        return False

    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
        try:
            os.killpg(pgid, 0)
            os.killpg(pgid, signal.SIGKILL)
        except OSError:
            return True
        return True
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
            return True
        except OSError:
            return False

async def kill_stale_tree_async(pid: int, expected_cmd: list[str]) -> bool:
    cmdline_path = f"/proc/{pid}/cmdline"
    try:
        raw = read_bytes(cmdline_path)
        actual = [arg.decode(errors="replace") for arg in raw.split(b"\x00") if arg]
    except (OSError, IOError):
        return False

    if not _command_matches(actual, expected_cmd):
        return False

    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
        await asyncio.sleep(0.05)
        try:
            os.killpg(pgid, 0)
            os.killpg(pgid, signal.SIGKILL)
        except OSError:
            return True
        return True
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
            return True
        except OSError:
            return False

_SIG_CACHE: dict[Callable[..., Awaitable[str]], tuple[set[str], bool]] = {}

def _filter_executor_kwargs(
    executor: Callable[..., Awaitable[str]],
    kwargs: dict[str, str | int | float | bool | list | dict | ResourcePermit | None],
    on_progress: Callable[[int, str, Optional[dict]], None],
) -> dict[str, str | int | float | bool | list | dict | ResourcePermit | None]:
    try:
        if executor not in _SIG_CACHE:
            sig = inspect.signature(executor)
            params = set(sig.parameters.keys())
            has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            _SIG_CACHE[executor] = (params, has_var_kw)
        params, has_var_kw = _SIG_CACHE[executor]
    except Exception:
        params, has_var_kw = set(), True

    target = dict(kwargs) if has_var_kw else {k: v for k, v in kwargs.items() if k in params}
    if "on_progress" in params or has_var_kw:
        target["on_progress"] = on_progress
    return target

class JobRunner:
    async def run(
        self,
        job: JobRecord,
        executor: Callable[..., Awaitable[str]],
        args: tuple = (),
        kwargs: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> Optional[str]:
        effective_timeout = timeout or Settings.JOB_MAX_RUNTIME
        request_id_ctx.set(job.job_id)
        set_telemetry(
            request_id=job.job_id,
            job_id=job.job_id,
            user_id=str(job.user_id) if job.user_id else None,
            service=job.service_type,
            client_ip=job.client_ip,
            endpoint=f"/api/v1/tools/{job.service_type.replace('_', '-')}",
        )
        job.started_at = time.monotonic()
        job.update(1, "Processing", JobStatus.PROCESSING)

        def on_progress(p: int, m: str, meta: Optional[dict] = None) -> None:
            job.update(p, m, metadata=meta)

        try:
            exec_kwargs = {**(kwargs or {})}
            if job.user_id:
                exec_kwargs["user_id"] = job.user_id
            target_kwargs = _filter_executor_kwargs(executor, exec_kwargs, on_progress)
            output = await asyncio.wait_for(
                executor(*args, **target_kwargs),
                timeout=effective_timeout,
            )
            job.complete(output)
            execution_ms = round((time.monotonic() - job.started_at) * 1000.0, 2)
            queue_wait_ms = round((job.started_at - job.created_at) * 1000.0, 2)
            logger.info(
                f"{{finish}}-{job.job_id} in {execution_ms / 1000.0:.1f}s",
                extra={
                    "duration_ms": execution_ms,
                    "queue_wait_ms": queue_wait_ms,
                    "job_id": job.job_id,
                    "service": job.service_type,
                    "user_id": str(job.user_id) if job.user_id else None,
                    "status": "completed",
                },
            )
            return output
        except (asyncio.TimeoutError, TimeoutError) as e:
            job.fail(f"Job execution timed out after {effective_timeout}s")
            logger.error(f"{{timeout}}-{job.job_id}: {e}")
            partial_dir = f"tmp/downloads/{job.job_id}"
            try:
                if exists(partial_dir):
                    delete(partial_dir)
            except OSError as cleanup_err:
                logger.warning(f"[{job.job_id}] Failed to clean partial directory: {cleanup_err}", exc_info=True)
            return None
        except Exception as e:
            job.fail(e)
            logger.error(f"{{failed}}-{job.job_id}: {e}", exc_info=True)
            partial_dir = f"tmp/downloads/{job.job_id}"
            try:
                if exists(partial_dir):
                    delete(partial_dir)
            except OSError as cleanup_err:
                logger.warning(f"[{job.job_id}] Failed to clean partial directory: {cleanup_err}", exc_info=True)
            return None
