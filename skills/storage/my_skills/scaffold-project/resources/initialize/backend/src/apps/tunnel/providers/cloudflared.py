from __future__ import annotations
import re
from typing import Optional
from src.config import Settings, setup_logger
from src.helpers import ExternalServiceError
from ..helpers import CliTunnelProcess, NotifyCallback, TunnelInstaller, normalize_public_url
from ..schema import TunnelEventType, TunnelProvider
from .base import BaseTunnelProvider

logger = setup_logger(Settings.LOG_DIR / "tunnel.log", name="apps.tunnel.cloudflared")

_TRYCLOUDFLARE_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
_NAMED_READY_RE = re.compile(r"Registered tunnel connection", re.IGNORECASE)


class CloudflaredProvider(BaseTunnelProvider):
    provider = TunnelProvider.CLOUDFLARED

    def __init__(
        self,
        target_host: str,
        target_port: int,
        timeout: float = 45.0,
        notify: Optional[NotifyCallback] = None,
        token: Optional[str] = None,
        hostname: Optional[str] = None,
    ) -> None:
        super().__init__(target_host=target_host, target_port=target_port, timeout=timeout, notify=notify)
        self._token = (token if token is not None else Settings.TUNNEL_CLOUDFLARE_TOKEN).strip()
        self._hostname = (hostname if hostname is not None else Settings.TUNNEL_CLOUDFLARE_HOSTNAME).strip()
        self._runner: Optional[CliTunnelProcess] = None

    def _build_command(self, binary_path: str) -> tuple[list[str], Optional[re.Pattern[str]], Optional[re.Pattern[str]]]:
        if self._token:
            cmd = [binary_path, "tunnel", "--no-autoupdate", "run", "--token", self._token]
            return cmd, None, _NAMED_READY_RE
        target_url = f"http://{self.target_host}:{self.target_port}"
        cmd = [binary_path, "tunnel", "--no-autoupdate", "--url", target_url]
        return cmd, _TRYCLOUDFLARE_RE, None

    def _resolve_named_url(self) -> str:
        if self._hostname:
            return normalize_public_url(self._hostname)
        if Settings.BACKEND_DOMAIN and Settings.BACKEND_DOMAIN not in {"127.0.0.1", "localhost"}:
            return normalize_public_url(Settings.BACKEND_DOMAIN)
        return f"http://{self.target_host}:{self.target_port}"

    def start(self) -> str:
        binary_path = TunnelInstaller.ensure_cloudflared(notify=self._notify)
        cmd, url_pattern, ready_marker = self._build_command(binary_path)
        self.emit(TunnelEventType.STARTING, f"Starting Cloudflare tunnel on {self.target_host}:{self.target_port}...")
        self._runner = CliTunnelProcess(
            label="Cloudflare Tunnel",
            command=cmd,
            url_pattern=url_pattern,
            timeout=self.timeout,
        )
        detected = self._runner.start(ready_marker=ready_marker)
        public_url = detected if detected else self._resolve_named_url()
        if not public_url:
            self.stop()
            raise ExternalServiceError("Cloudflared", "Tunnel started without a resolvable public URL")
        self.tunnel_url = public_url
        self.emit(TunnelEventType.URL_READY, "Cloudflare Tunnel URL is ready", public_url)
        logger.info(f"tunnel.cloudflared.ready url={public_url} target={self.target_host}:{self.target_port}")
        return public_url

    def is_alive(self) -> bool:
        return self._runner is not None and self._runner.is_alive()

    def stop(self) -> bool:
        if self._runner is not None:
            self._runner.stop()
            self._runner = None
        self.tunnel_url = None
        self.emit(TunnelEventType.STOPPED, "Cloudflare Tunnel stopped")
        return True
