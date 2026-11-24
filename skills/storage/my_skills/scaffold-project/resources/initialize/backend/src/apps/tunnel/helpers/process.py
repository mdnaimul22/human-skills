from __future__ import annotations
import queue
import re
import subprocess
import threading
import time
from collections import deque
from typing import Callable, Optional
from src.config import Settings, setup_logger
from src.helpers import ExternalServiceError

logger = setup_logger(Settings.LOG_DIR / "tunnel.log", name="apps.tunnel.process")

LineCallback = Callable[[str], None]


class CliTunnelProcess:
    def __init__(
        self,
        label: str,
        command: list[str],
        url_pattern: Optional[re.Pattern[str]] = None,
        shutdown_command: Optional[list[str]] = None,
        timeout: float = 45.0,
        on_line: Optional[LineCallback] = None,
    ) -> None:
        self.label = label
        self.command = list(command)
        self.url_pattern = url_pattern
        self.shutdown_command = list(shutdown_command) if shutdown_command else None
        self.timeout = timeout
        self.on_line = on_line
        self._process: Optional[subprocess.Popen[str]] = None
        self._recent_output: deque[str] = deque(maxlen=12)

    def _extract_url(self, line: str) -> Optional[str]:
        if self.url_pattern is None:
            return None
        match = self.url_pattern.search(line)
        if not match:
            return None
        group_idx = 1 if match.lastindex else 0
        return match.group(group_idx).rstrip(".,)")

    def _spawn_reader(self, out_queue: queue.Queue[str]) -> None:
        proc = self._process
        if proc is None or proc.stdout is None:
            return

        def _reader() -> None:
            if proc.stdout is None:
                return
            for raw_line in proc.stdout:
                out_queue.put(raw_line)

        threading.Thread(target=_reader, daemon=True).start()

    def _handle_line(self, line: str) -> Optional[str]:
        cleaned = line.strip()
        if not cleaned:
            return None
        self._recent_output.append(cleaned)
        if self.on_line is not None:
            try:
                self.on_line(cleaned)
            except Exception as err:
                logger.debug(f"tunnel.process.line_callback_err label={self.label} err={err}")
        return self._extract_url(cleaned)

    def start(self, ready_marker: Optional[re.Pattern[str]] = None) -> Optional[str]:
        self._recent_output.clear()
        self._process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        out_queue: queue.Queue[str] = queue.Queue()
        self._spawn_reader(out_queue)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            try:
                line = out_queue.get(timeout=0.1)
            except queue.Empty:
                if self._process.poll() is not None:
                    break
                continue
            url = self._handle_line(line)
            if url:
                return url
            if ready_marker is not None and ready_marker.search(line):
                return ""
        details = " ".join(self._recent_output)
        if self._process.poll() is not None:
            msg = f"{self.label} exited prematurely (code={self._process.returncode})"
            raise ExternalServiceError(self.label, f"{msg}: {details}" if details else msg)
        self.terminate()
        msg = f"{self.label} timed out after {self.timeout:.0f}s"
        raise ExternalServiceError(self.label, f"{msg}: {details}" if details else msg)

    def is_alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def terminate(self) -> None:
        proc = self._process
        if proc is None:
            return
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=3.0)
                except subprocess.TimeoutExpired as err:
                    logger.warning(f"tunnel.process.kill_timeout label={self.label} err={err}")
        self._process = None

    def stop(self) -> bool:
        self.terminate()
        if self.shutdown_command:
            try:
                subprocess.run(
                    self.shutdown_command,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10.0,
                )
            except (OSError, subprocess.TimeoutExpired) as err:
                logger.warning(f"tunnel.process.shutdown_cmd_err label={self.label} err={err}")
        return True
