from __future__ import annotations
import subprocess
import time
from src.config import Settings, delete, exists, get_mtime, setup_logger
from src.apps.git.schema import GitCommandResult

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.providers.git")
_STALE_LOCK_SECONDS = 5.0


def _extract_lock_path(err: str, cwd: str) -> str | None:
    if "'" in err:
        for part in err.split("'"):
            if part.endswith(".lock"):
                candidate = part if part.startswith("/") else f"{cwd}/{part}"
                if exists(candidate):
                    return candidate
    candidate = f"{cwd}/.git/index.lock"
    return candidate if exists(candidate) else None


def _clean_stale_lock(err: str, cwd: str) -> bool:
    if "index.lock" not in err and ".lock': File exists" not in err:
        return False
    lock_file = _extract_lock_path(err, cwd)
    if not lock_file or not exists(lock_file):
        return False
    try:
        age = time.time() - get_mtime(lock_file)
        if age > _STALE_LOCK_SECONDS:
            logger.warning(f"Clearing stale git lock (age {age:.1f}s): {lock_file}")
            delete(lock_file)
            return True
    except (OSError, ValueError) as e:
        logger.warning(f"Could not remove git lock file {lock_file}: {e}")
    return False


def _exec_git(args: list[str], cwd: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_git(args: list[str], cwd: str, timeout: int | None = None) -> GitCommandResult:
    effective_timeout = timeout if timeout is not None else Settings.GIT_TIMEOUT_SECONDS
    try:
        proc = _exec_git(args, cwd, effective_timeout)
        if proc.returncode == 0:
            return GitCommandResult(ok=True, output=proc.stdout.rstrip("\r\n"))
        err = proc.stderr.strip() or proc.stdout.strip()
        if _clean_stale_lock(err, cwd):
            retry = _exec_git(args, cwd, effective_timeout)
            if retry.returncode == 0:
                return GitCommandResult(ok=True, output=retry.stdout.rstrip("\r\n"))
            return GitCommandResult(ok=False, output=retry.stderr.strip() or retry.stdout.strip())
        return GitCommandResult(ok=False, output=err)
    except subprocess.TimeoutExpired:
        return GitCommandResult(ok=False, output=f"git timed out after {effective_timeout}s")
    except OSError as e:
        logger.error(f"Git command failed: {e}")
        return GitCommandResult(ok=False, output=str(e))


def repo_is_dirty(repo_path: str) -> bool:
    res = run_git(["status", "--porcelain", "-uall"], repo_path)
    return res.ok and bool(res.output.strip())


def get_status(repo_path: str) -> GitCommandResult:
    return run_git(["status", "--porcelain", "-uall"], repo_path)
