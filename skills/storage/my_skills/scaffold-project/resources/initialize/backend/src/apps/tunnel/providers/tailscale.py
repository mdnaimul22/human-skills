from __future__ import annotations
import json
import os
import re
import signal
import subprocess
import threading
import time
from collections import deque
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from src.config import Settings, delete, ensure_dir, exists, get_abs_path, read_text, setup_logger, sys_read_bytes, write_text
from src.helpers import ExternalServiceError
from ..helpers import CliTunnelProcess, NotifyCallback, TunnelInstaller, normalize_public_url
from ..schema import TunnelEventType, TunnelProvider
from .base import BaseTunnelProvider

logger = setup_logger(Settings.LOG_DIR / "tunnel.log", name="apps.tunnel.tailscale")

_TS_URL_RE = re.compile(r"https://[a-zA-Z0-9.-]+\.ts\.net[^\s\"']*")
_TS_LOGIN_RE = re.compile(r"https://login\.tailscale\.com/[^\s\"']+")
_RUNTIME_DIR_REL = "data/apps/tunnel/runtime"
_STATE_DIR_REL = "data/apps/tunnel/tailscale"
_SOCKET_REL = f"{_RUNTIME_DIR_REL}/tailscaled.sock"
_PID_REL = f"{_RUNTIME_DIR_REL}/tailscaled.pid"
_DAEMON_MARKERS: tuple[str, ...] = (
    "failed to connect to local tailscaled",
    "tailscaled.sock",
    "no such file or directory",
    "connection refused",
    "is tailscaled running",
)


def _compact(parts: list[str]) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


def _is_daemon_down_msg(output: str) -> bool:
    low = output.lower()
    return any(marker in low for marker in _DAEMON_MARKERS)


def _ts_cmd(binary_path: str, args: list[str], socket_abs: Optional[str]) -> list[str]:
    prefix = ["--socket", socket_abs] if socket_abs else []
    return [binary_path, *prefix, *args]


def _run_ts(binary_path: str, args: list[str], socket_abs: Optional[str], timeout: float = 12.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _ts_cmd(binary_path, args, socket_abs),
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def _daemon_ready(binary_path: str, socket_abs: Optional[str]) -> bool:
    res = _run_ts(binary_path, ["status", "--json"], socket_abs)
    return not _is_daemon_down_msg(_compact([res.stderr, res.stdout]))


class TailscaleSelfNode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dns_name: str = Field(default="", alias="DNSName")


class TailscaleStatusPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    backend_state: str = Field(default="", alias="BackendState")
    self_node: TailscaleSelfNode = Field(default_factory=TailscaleSelfNode, alias="Self")


def _parse_status_json(raw: str) -> TailscaleStatusPayload:
    try:
        parsed = json.loads(raw or "{}")
        return TailscaleStatusPayload.model_validate(parsed)
    except Exception:
        return TailscaleStatusPayload()


def _extract_dns_url(status_data: TailscaleStatusPayload) -> Optional[str]:
    clean = status_data.self_node.dns_name.strip().rstrip(".")
    return normalize_public_url(clean) if clean else None


def _is_tailscaled_pid(pid: int) -> bool:
    try:
        cmdline = sys_read_bytes(f"/proc/{pid}/cmdline").decode("utf-8", errors="replace")
    except OSError:
        return False
    return "tailscaled" in cmdline


def _terminate_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    waiter = threading.Event()
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            return
        waiter.wait(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError as err:
        logger.debug(f"tunnel.tailscale.sigkill_err pid={pid} err={err}")


def _drain_stream(proc: subprocess.Popen[str], ring: deque[str]) -> None:
    if proc.stdout is None:
        return
    for line in proc.stdout:
        cleaned = line.strip()
        if cleaned:
            ring.append(cleaned)


class TailscaleProvider(BaseTunnelProvider):
    provider = TunnelProvider.TAILSCALE

    def __init__(
        self,
        target_host: str,
        target_port: int,
        timeout: float = 45.0,
        notify: Optional[NotifyCallback] = None,
        authkey: Optional[str] = None,
        https_port: Optional[int] = None,
    ) -> None:
        super().__init__(target_host=target_host, target_port=target_port, timeout=timeout, notify=notify)
        self._authkey = (authkey if authkey is not None else Settings.TUNNEL_TAILSCALE_AUTHKEY).strip()
        self._https_port = https_port if https_port is not None else Settings.TUNNEL_TAILSCALE_HTTPS_PORT
        self._runner: Optional[CliTunnelProcess] = None
        self._socket_abs: Optional[str] = None
        self._managed_daemon: bool = False
        self._announced_logins: set[str] = set()

    def _start_managed_daemon(self, cli_bin: str, daemon_bin: Optional[str]) -> str:
        if not daemon_bin:
            raise ExternalServiceError("Tailscale", "tailscaled binary unavailable and system daemon is not running")
        ensure_dir(_RUNTIME_DIR_REL)
        ensure_dir(_STATE_DIR_REL)
        socket_abs = get_abs_path(_SOCKET_REL)
        if _daemon_ready(cli_bin, socket_abs):
            self._managed_daemon = True
            return socket_abs
        if exists(_SOCKET_REL):
            delete(_SOCKET_REL)
        self.emit(TunnelEventType.INFO, "Starting userspace tailscaled background service...")
        state_dir_abs = get_abs_path(_STATE_DIR_REL)
        state_file_abs = get_abs_path(f"{_STATE_DIR_REL}/tailscaled.state")
        ring: deque[str] = deque(maxlen=12)
        proc = subprocess.Popen(
            [
                daemon_bin,
                "--tun=userspace-networking",
                "--socket", socket_abs,
                "--statedir", state_dir_abs,
                "--state", state_file_abs,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        threading.Thread(target=_drain_stream, args=(proc, ring), daemon=True).start()
        write_text(_PID_REL, str(proc.pid))
        waiter = threading.Event()
        deadline = time.monotonic() + 12.0
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            if _daemon_ready(cli_bin, socket_abs):
                self._managed_daemon = True
                return socket_abs
            waiter.wait(0.25)
        if proc.poll() is None:
            _terminate_pid(proc.pid)
        if exists(_PID_REL):
            delete(_PID_REL)
        details = _compact(list(ring))
        raise ExternalServiceError("Tailscale", f"Failed to start userspace tailscaled: {details}" if details else "Failed to start userspace tailscaled")

    def _stop_managed_daemon(self) -> None:
        if exists(_PID_REL):
            try:
                pid = int(read_text(_PID_REL).strip())
            except (OSError, ValueError):
                pid = 0
            if pid > 0 and _is_tailscaled_pid(pid):
                _terminate_pid(pid)
            delete(_PID_REL)
        if exists(_SOCKET_REL):
            delete(_SOCKET_REL)
        self._managed_daemon = False

    def _on_output_line(self, line: str) -> None:
        match = _TS_LOGIN_RE.search(line)
        if not match:
            return
        url = match.group(0).rstrip(".,)")
        if url in self._announced_logins:
            return
        self._announced_logins.add(url)
        logger.warning(f"tunnel.tailscale.login_required url={url}")
        self.emit(TunnelEventType.LOGIN_REQUIRED, f"Approve Tailscale login URL: {url}", url)

    def _run_tailscale_up(self, cli_bin: str, socket_abs: Optional[str]) -> None:
        args = ["up", f"--authkey={self._authkey}"] if self._authkey else ["up"]
        cmd = _ts_cmd(cli_bin, args, socket_abs)
        self.emit(TunnelEventType.INFO, "Joining tailnet via `tailscale up`...")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        recent: deque[str] = deque(maxlen=10)
        deadline = time.monotonic() + self.timeout
        if proc.stdout is not None:
            for raw_line in proc.stdout:
                cleaned = raw_line.strip()
                if cleaned:
                    recent.append(cleaned)
                    self._on_output_line(cleaned)
                if time.monotonic() >= deadline:
                    proc.terminate()
                    raise ExternalServiceError("Tailscale", f"`tailscale up` timed out: {_compact(list(recent))}")
        code = proc.wait(timeout=5.0)
        if code != 0:
            raise ExternalServiceError("Tailscale", f"`tailscale up` failed (code={code}): {_compact(list(recent))}")

    def _ensure_ready(self, cli_bin: str, daemon_bin: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        socket_abs: Optional[str] = None
        res = _run_ts(cli_bin, ["status", "--json"], None)
        if res.returncode != 0 and _is_daemon_down_msg(_compact([res.stderr, res.stdout])):
            socket_abs = self._start_managed_daemon(cli_bin, daemon_bin)
            res = _run_ts(cli_bin, ["status", "--json"], socket_abs)
        status_data = _parse_status_json(res.stdout)
        backend_state = status_data.backend_state.lower()
        if res.returncode != 0 or (backend_state and backend_state != "running"):
            self._run_tailscale_up(cli_bin, socket_abs)
            res = _run_ts(cli_bin, ["status", "--json"], socket_abs)
            status_data = _parse_status_json(res.stdout)
            backend_state = status_data.backend_state.lower()
            if res.returncode != 0 or (backend_state and backend_state != "running"):
                raise ExternalServiceError("Tailscale", f"Tailscale node not ready (state='{backend_state or 'unknown'}')")
        help_res = _run_ts(cli_bin, ["funnel", "--help"], socket_abs)
        help_out = _compact([help_res.stderr, help_res.stdout]).lower()
        if help_res.returncode != 0 or "funnel" not in help_out:
            raise ExternalServiceError("Tailscale", "Installed Tailscale CLI does not support `tailscale funnel`")
        return socket_abs, _extract_dns_url(status_data)

    def start(self) -> str:
        cli_bin, daemon_bin = TunnelInstaller.ensure_tailscale(notify=self._notify)
        self._announced_logins.clear()
        socket_abs, dns_url = self._ensure_ready(cli_bin, daemon_bin)
        self._socket_abs = socket_abs
        target = f"http://{self.target_host}:{self.target_port}"
        start_cmd = _ts_cmd(cli_bin, ["funnel", "--yes", f"--https={self._https_port}", target], socket_abs)
        stop_cmd = _ts_cmd(cli_bin, ["funnel", "--yes", f"--https={self._https_port}", target, "off"], socket_abs)
        self.emit(TunnelEventType.STARTING, f"Starting Tailscale Funnel on {self.target_host}:{self.target_port}...")
        self._runner = CliTunnelProcess(
            label="Tailscale Funnel",
            command=start_cmd,
            url_pattern=_TS_URL_RE,
            shutdown_command=stop_cmd,
            timeout=self.timeout,
            on_line=self._on_output_line,
        )
        detected = self._runner.start()
        public_url = detected or dns_url or ""
        if not public_url:
            self.stop()
            raise ExternalServiceError("Tailscale", "Tailscale Funnel did not return a public URL")
        self.tunnel_url = public_url
        self.emit(TunnelEventType.URL_READY, "Tailscale Funnel URL is ready", public_url)
        logger.info(f"tunnel.tailscale.ready url={public_url} target={self.target_host}:{self.target_port}")
        return public_url

    def is_alive(self) -> bool:
        return self._runner is not None and self._runner.is_alive()

    def stop(self) -> bool:
        try:
            if self._runner is not None:
                self._runner.stop()
                self._runner = None
            return True
        finally:
            if self._managed_daemon:
                self._stop_managed_daemon()
            self._socket_abs = None
            self.tunnel_url = None
            self.emit(TunnelEventType.STOPPED, "Tailscale Funnel stopped")
