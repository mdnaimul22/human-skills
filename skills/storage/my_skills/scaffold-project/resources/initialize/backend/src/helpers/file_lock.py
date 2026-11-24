import asyncio
import io
import sys
import time
import types
from typing import Optional
from src.config import ensure_dir, get_abs_path, setup_logger, Settings, delete

if sys.platform != "win32":
    import fcntl
else:
    fcntl = None

logger = setup_logger(Settings.LOG_DIR / "helpers.log", name="helpers.file_lock")


class AsyncFileLock:
    def __init__(self, filepath: str, timeout: float = 60.0) -> None:
        self.filepath = filepath
        self.timeout = timeout
        self.fd: Optional[io.TextIOWrapper] = None

    def _safe_close(self) -> None:
        if self.fd:
            try:
                self.fd.close()
            except OSError as err:
                logger.debug("Safe close error for %s: %s", self.filepath, err)
            self.fd = None

    async def __aenter__(self) -> "AsyncFileLock":
        parent_dir = self.filepath.rsplit("/", 1)[0] if "/" in self.filepath else "."
        ensure_dir(parent_dir)
        self.fd = io.open(get_abs_path(self.filepath), "a")
        start_time = time.monotonic()
        backoff = 0.05
        while True:
            try:
                if fcntl is not None:
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except (BlockingIOError, PermissionError):
                if time.monotonic() - start_time >= self.timeout:
                    self._safe_close()
                    raise TimeoutError(f"Failed to acquire file lock for {self.filepath} within {self.timeout}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 0.5)
            except BaseException:
                self._safe_close()
                raise

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        if self.fd:
            try:
                if fcntl is not None:
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            except OSError as err:
                logger.debug("Lock release error: %s", err)
            self._safe_close()


class SyncFileLock:
    def __init__(self, filepath: str, non_blocking: bool = False) -> None:
        self.filepath = filepath
        self.non_blocking = non_blocking
        self.fd: Optional[io.TextIOWrapper] = None
        self.acquired: bool = False

    def _safe_close(self) -> None:
        if self.fd:
            try:
                self.fd.close()
            except OSError as err:
                logger.debug("Lock close error: %s", err)
            self.fd = None

    def __enter__(self) -> "SyncFileLock":
        parent_dir = self.filepath.rsplit("/", 1)[0] if "/" in self.filepath else "."
        ensure_dir(parent_dir)
        self.fd = io.open(get_abs_path(self.filepath), "a")
        if fcntl is not None:
            flags = fcntl.LOCK_EX
            if self.non_blocking:
                flags |= fcntl.LOCK_NB
            try:
                fcntl.flock(self.fd.fileno(), flags)
                self.acquired = True
            except (BlockingIOError, PermissionError):
                self.acquired = False
        else:
            self.acquired = True
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        if self.fd:
            if self.acquired and fcntl is not None:
                try:
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                except OSError as err:
                    logger.debug("Lock release error: %s", err)
            self._safe_close()


def try_clean_and_remove_stale_lock(lock_path: str) -> bool:
    try:
        fd = io.open(get_abs_path(lock_path), "a")
        try:
            if fcntl is not None:
                fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            delete(lock_path)
            if fcntl is not None:
                fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
            fd.close()
            return True
        except (BlockingIOError, PermissionError):
            fd.close()
            return False
    except OSError as err:
        logger.debug("Stale lock cleanup error: %s", err)
        return False


def try_clean_stale_lock(lock_path: str) -> bool:
    return try_clean_and_remove_stale_lock(lock_path)
