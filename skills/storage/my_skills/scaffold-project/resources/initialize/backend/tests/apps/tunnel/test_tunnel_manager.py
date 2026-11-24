from __future__ import annotations
import asyncio
from typing import Optional
import pytest
from src.apps.tunnel import TunnelManager, TunnelProvider, TunnelState, get_tunnel_manager
from src.apps.tunnel.providers import BaseTunnelProvider
from src.config import EnvHotReloader, Settings, delete, exists, write_text


class _StubProvider(BaseTunnelProvider):
    def __init__(self, provider: TunnelProvider, url: str, target_host: str, target_port: int) -> None:
        super().__init__(target_host=target_host, target_port=target_port)
        self.provider = provider
        self._url = url
        self.alive = False
        self.start_calls = 0
        self.stop_calls = 0

    def start(self) -> str:
        self.start_calls += 1
        self.alive = True
        self.tunnel_url = self._url
        return self._url

    def is_alive(self) -> bool:
        return self.alive

    def stop(self) -> bool:
        self.stop_calls += 1
        self.alive = False
        self.tunnel_url = None
        return True


def setup_function() -> None:
    TunnelManager.reset_instance()
    EnvHotReloader.reset_instance()


@pytest.mark.asyncio
async def test_manager_disabled_via_master_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Settings, "TUNNEL_MANAGER", False)
    monkeypatch.setattr(Settings, "TUNNEL", True)
    mgr = get_tunnel_manager()
    url = await mgr.start_async()
    assert url is None
    assert mgr.get_status().state == TunnelState.DISABLED
    assert mgr._watch_task is None
    await mgr.stop_async()


@pytest.mark.asyncio
async def test_manager_standby_when_tunnel_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Settings, "TUNNEL_MANAGER", True)
    monkeypatch.setattr(Settings, "TUNNEL", False)
    monkeypatch.setattr(Settings, "TUNNEL_POLL_INTERVAL_SEC", 0.05)
    mgr = get_tunnel_manager()
    try:
        url = await mgr.start_async()
        assert url is None
        status = mgr.get_status()
        assert status.state == TunnelState.STANDBY
        assert status.manager_enabled is True
        assert status.tunnel_enabled is False
        assert mgr._watch_task is not None and not mgr._watch_task.done()
    finally:
        await mgr.stop_async()


@pytest.mark.asyncio
async def test_manager_activates_and_hot_reloads_env_toggles(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_rel = "data/apps/tunnel/test_hot_reload.env"
    created: list[_StubProvider] = []

    def fake_create(
        provider: TunnelProvider,
        target_host: str,
        target_port: int,
        timeout: float,
        notify: Optional[object] = None,
    ) -> _StubProvider:
        url = "https://alpha.trycloudflare.com" if provider == TunnelProvider.CLOUDFLARED else "https://node.ts.net"
        stub = _StubProvider(provider=provider, url=url, target_host=target_host, target_port=target_port)
        created.append(stub)
        return stub

    monkeypatch.setattr("src.apps.tunnel.manager.create_provider", fake_create)
    monkeypatch.setattr(Settings, "TUNNEL_CONFIG_FILE", cfg_rel)
    monkeypatch.setattr(Settings, "TUNNEL_MANAGER", True)
    monkeypatch.setattr(Settings, "TUNNEL", False)
    monkeypatch.setattr(Settings, "TUNNEL_PROVIDER", "cloudflared")
    monkeypatch.setattr(Settings, "TUNNEL_TARGET_PORT", 0)
    monkeypatch.setattr(Settings, "TUNNEL_POLL_INTERVAL_SEC", 60.0)

    write_text(cfg_rel, "TUNNEL_MANAGER=true\nTUNNEL=false\nTUNNEL_PROVIDER=cloudflared\n")
    mgr = get_tunnel_manager()
    try:
        await mgr.start_async()
        assert mgr.get_status().state == TunnelState.STANDBY

        write_text(cfg_rel, "TUNNEL_MANAGER=true\nTUNNEL=true\nTUNNEL_PROVIDER=cloudflared\n")
        assert await mgr.poll_once_async() is True
        assert mgr.get_status().state == TunnelState.ACTIVE
        assert mgr.get_tunnel_url() == "https://alpha.trycloudflare.com"
        assert mgr.get_active_origin() == "https://alpha.trycloudflare.com"
        assert Settings.PUBLIC_URL == "https://alpha.trycloudflare.com"

        write_text(cfg_rel, "TUNNEL_MANAGER=true\nTUNNEL=true\nTUNNEL_PROVIDER=tailscale\n")
        assert await mgr.poll_once_async() is True
        assert mgr.get_tunnel_url() == "https://node.ts.net"
        assert created[0].stop_calls >= 1

        write_text(cfg_rel, "TUNNEL_MANAGER=true\nTUNNEL=false\nTUNNEL_PROVIDER=tailscale\n")
        assert await mgr.poll_once_async() is True
        assert mgr.get_status().state == TunnelState.STANDBY
        assert mgr.get_tunnel_url() is None
        assert Settings.PUBLIC_URL is None
    finally:
        await mgr.stop_async()
        if exists(cfg_rel):
            delete(cfg_rel)


@pytest.mark.asyncio
async def test_manager_watchdog_restarts_crashed_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[_StubProvider] = []

    def fake_create(
        provider: TunnelProvider,
        target_host: str,
        target_port: int,
        timeout: float,
        notify: Optional[object] = None,
    ) -> _StubProvider:
        stub = _StubProvider(
            provider=provider,
            url=f"https://recover-{len(created)}.trycloudflare.com",
            target_host=target_host,
            target_port=target_port,
        )
        created.append(stub)
        return stub

    monkeypatch.setattr("src.apps.tunnel.manager.create_provider", fake_create)
    monkeypatch.setattr(Settings, "TUNNEL_MANAGER", True)
    monkeypatch.setattr(Settings, "TUNNEL", True)
    monkeypatch.setattr(Settings, "TUNNEL_AUTO_RESTART", True)
    monkeypatch.setattr(Settings, "TUNNEL_MAX_RESTARTS", 3)
    monkeypatch.setattr(Settings, "TUNNEL_POLL_INTERVAL_SEC", 60.0)

    mgr = get_tunnel_manager()
    monkeypatch.setattr(mgr, "_compute_backoff_sec", lambda: 0.0)
    try:
        url1 = await mgr.start_async()
        assert url1 == "https://recover-0.trycloudflare.com"
        created[0].alive = False

        await mgr._run_watchdog_tick()
        assert len(created) == 2
        assert mgr.get_tunnel_url() == "https://recover-1.trycloudflare.com"
        assert mgr.get_status().state == TunnelState.ACTIVE
    finally:
        await mgr.stop_async()
