from __future__ import annotations
import subprocess
from unittest.mock import MagicMock, patch
import pytest
from src.apps.tunnel.providers import CloudflaredProvider, TailscaleProvider
from src.apps.tunnel.schema import TunnelEventType


def test_cloudflared_quick_tunnel_extracts_trycloudflare_url() -> None:
    events: list[tuple[TunnelEventType, str, str | None]] = []

    class _FakeRunner:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs
            self.alive = True

        def start(self, ready_marker: object = None) -> str:
            return "https://fast-cat-123.trycloudflare.com"

        def is_alive(self) -> bool:
            return self.alive

        def stop(self) -> bool:
            self.alive = False
            return True

    with patch("src.apps.tunnel.providers.cloudflared.TunnelInstaller.ensure_cloudflared", return_value="/usr/bin/cloudflared"), patch(
        "src.apps.tunnel.providers.cloudflared.CliTunnelProcess", _FakeRunner
    ):
        provider = CloudflaredProvider(
            target_host="127.0.0.1",
            target_port=8000,
            token="",
            notify=lambda ev, msg, url: events.append((ev, msg, url)),
        )
        url = provider.start()
        assert url == "https://fast-cat-123.trycloudflare.com"
        assert provider.is_alive() is True
        assert any(ev == TunnelEventType.URL_READY and u == url for ev, _, u in events)
        assert provider.stop() is True
        assert provider.is_alive() is False


def test_cloudflared_named_token_tunnel_uses_configured_hostname() -> None:
    captured_cmd: list[str] = []

    class _FakeRunner:
        def __init__(self, label: str, command: list[str], **_kwargs: object) -> None:
            captured_cmd.extend(command)
            self.alive = True

        def start(self, ready_marker: object = None) -> str:
            assert ready_marker is not None
            return ""

        def is_alive(self) -> bool:
            return self.alive

        def stop(self) -> bool:
            self.alive = False
            return True

    with patch("src.apps.tunnel.providers.cloudflared.TunnelInstaller.ensure_cloudflared", return_value="/usr/bin/cloudflared"), patch(
        "src.apps.tunnel.providers.cloudflared.CliTunnelProcess", _FakeRunner
    ):
        provider = CloudflaredProvider(
            target_host="127.0.0.1",
            target_port=8000,
            token="eyJ-test-token",
            hostname="api.example.com",
        )
        url = provider.start()
        assert url == "https://api.example.com"
        assert "--token" in captured_cmd
        assert "eyJ-test-token" in captured_cmd
        assert provider.stop() is True


def test_tailscale_provider_uses_running_system_daemon_and_funnel() -> None:
    status_json = '{"BackendState":"Running","Self":{"DNSName":"box.tailnet.ts.net."}}'

    def fake_run_ts(cli: str, args: list[str], socket_abs: str | None, timeout: float = 12.0) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["status", "--json"]:
            return subprocess.CompletedProcess([cli, *args], 0, stdout=status_json, stderr="")
        if args[:2] == ["funnel", "--help"]:
            return subprocess.CompletedProcess([cli, *args], 0, stdout="USAGE: tailscale funnel", stderr="")
        return subprocess.CompletedProcess([cli, *args], 0, stdout="", stderr="")

    class _FakeRunner:
        def __init__(self, **_kwargs: object) -> None:
            self.alive = True

        def start(self, ready_marker: object = None) -> str:
            return "https://box.tailnet.ts.net"

        def is_alive(self) -> bool:
            return self.alive

        def stop(self) -> bool:
            self.alive = False
            return True

    with patch("src.apps.tunnel.providers.tailscale.TunnelInstaller.ensure_tailscale", return_value=("/usr/bin/tailscale", "/usr/sbin/tailscaled")), patch(
        "src.apps.tunnel.providers.tailscale._run_ts", side_effect=fake_run_ts
    ), patch("src.apps.tunnel.providers.tailscale.CliTunnelProcess", _FakeRunner):
        provider = TailscaleProvider(target_host="127.0.0.1", target_port=8000)
        url = provider.start()
        assert url == "https://box.tailnet.ts.net"
        assert provider.is_alive() is True
        assert provider.stop() is True
        assert provider.is_alive() is False
