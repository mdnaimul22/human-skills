from __future__ import annotations
import os
import uuid
import pytest
from src.config import EnvHotReloader, Settings, delete, exists, write_text
from src.providers import ProxyManager, ProxyProviderType, ProxyState, get_proxy_manager
from src.providers.proxy.helpers import parse_static_proxies, parse_webshare_lines


def setup_function() -> None:
    ProxyManager.reset_instance()
    EnvHotReloader.reset_instance()


def test_parsers_handle_webshare_and_static_formats() -> None:
    raw_ws = "10.0.0.1:8080:alice:secret1\n10.0.0.2:8080:bob:secret2\n# comment\ninvalid\n"
    assert parse_webshare_lines(raw_ws) == [
        "http://alice:secret1@10.0.0.1:8080",
        "http://bob:secret2@10.0.0.2:8080",
    ]
    assert parse_static_proxies("http://a:b@1.1.1.1:80, socks5://2.2.2.2:1080, bad") == [
        "http://a:b@1.1.1.1:80",
        "socks5://2.2.2.2:1080",
    ]


@pytest.mark.asyncio
async def test_proxy_manager_disabled_via_master_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Settings, "PROXY_MANAGER", False)
    monkeypatch.setattr(Settings, "PROXY", True)
    mgr = get_proxy_manager()
    assert await mgr.start_async() is False
    assert mgr.get_status().state == ProxyState.DISABLED
    assert mgr.get_proxy() is None
    assert mgr._watch_task is None
    await mgr.stop_async()


@pytest.mark.asyncio
async def test_proxy_manager_standby_and_hot_reload_toggle(monkeypatch: pytest.MonkeyPatch) -> None:
    uid = f"{os.getpid()}_{uuid.uuid4().hex[:6]}"
    cfg_rel = f"tmp/test_tmp/proxy_cfg_{uid}.env"
    cache_rel = f"tmp/test_tmp/proxy_cache_{uid}.json"
    state_rel = f"tmp/test_tmp/proxy_state_{uid}.json"

    monkeypatch.setattr(Settings, "PROXY_CONFIG_FILE", cfg_rel)
    monkeypatch.setattr(Settings, "PROXY_CACHE_PATH", cache_rel)
    monkeypatch.setattr(Settings, "PROXY_STATE_PATH", state_rel)
    monkeypatch.setattr(Settings, "PROXY_MANAGER", True)
    monkeypatch.setattr(Settings, "PROXY", False)
    monkeypatch.setattr(Settings, "PROXY_PROVIDER", "static")
    monkeypatch.setattr(Settings, "PROXY_STATIC_URLS", "http://u:p@10.0.0.1:8080,http://u:p@10.0.0.2:8080")
    monkeypatch.setattr(Settings, "PROXY_POLL_INTERVAL_SEC", 60.0)

    write_text(
        cfg_rel,
        "PROXY_MANAGER=true\nPROXY=false\nPROXY_PROVIDER=static\n"
        "PROXY_STATIC_URLS=http://u:p@10.0.0.1:8080,http://u:p@10.0.0.2:8080\n",
    )
    mgr = get_proxy_manager()
    try:
        assert await mgr.start_async() is True
        assert mgr.get_status().state == ProxyState.STANDBY
        assert mgr.get_proxy() is None

        write_text(
            cfg_rel,
            "PROXY_MANAGER=true\nPROXY=true\nPROXY_PROVIDER=static\n"
            "PROXY_STATIC_URLS=http://u:p@10.0.0.1:8080,http://u:p@10.0.0.2:8080\n",
        )
        assert await mgr.poll_once_async() is True
        status = mgr.get_status()
        assert status.state == ProxyState.ACTIVE
        assert status.provider == ProxyProviderType.STATIC
        assert status.total_proxies == 2
        assert status.healthy_proxies == 2
        assert exists(cache_rel)

        p1 = mgr.get_proxy()
        p2 = mgr.get_proxy()
        assert {p1, p2} == {"http://u:p@10.0.0.1:8080", "http://u:p@10.0.0.2:8080"}

        write_text(cfg_rel, "PROXY_MANAGER=true\nPROXY=false\nPROXY_PROVIDER=static\n")
        assert await mgr.poll_once_async() is True
        assert mgr.get_status().state == ProxyState.STANDBY
        assert mgr.get_proxy() is None
    finally:
        await mgr.stop_async()
        for rel in (cfg_rel, cache_rel, state_rel):
            if exists(rel):
                delete(rel)


@pytest.mark.asyncio
async def test_proxy_manager_failure_cooldown_and_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    uid = f"{os.getpid()}_{uuid.uuid4().hex[:6]}"
    cache_rel = f"tmp/test_tmp/proxy_cd_cache_{uid}.json"
    state_rel = f"tmp/test_tmp/proxy_cd_state_{uid}.json"

    monkeypatch.setattr(Settings, "PROXY_CACHE_PATH", cache_rel)
    monkeypatch.setattr(Settings, "PROXY_STATE_PATH", state_rel)
    monkeypatch.setattr(Settings, "PROXY_MANAGER", True)
    monkeypatch.setattr(Settings, "PROXY", True)
    monkeypatch.setattr(Settings, "PROXY_PROVIDER", "static")
    monkeypatch.setattr(Settings, "PROXY_STATIC_URLS", "http://u:p@10.0.0.1:8080,http://u:p@10.0.0.2:8080")
    monkeypatch.setattr(Settings, "PROXY_MAX_FAILURES", 2)
    monkeypatch.setattr(Settings, "PROXY_COOLDOWN_SEC", 60.0)
    monkeypatch.setattr(Settings, "PROXY_POLL_INTERVAL_SEC", 60.0)

    mgr = get_proxy_manager()
    try:
        assert await mgr.start_async() is True
        bad = "http://u:p@10.0.0.1:8080"
        good = "http://u:p@10.0.0.2:8080"
        mgr.report_failure(bad)
        mgr.report_failure(bad)
        assert mgr.get_status().cooldown_proxies == 1
        assert mgr.get_proxy() == good
        assert mgr.get_proxy() == good

        mgr.report_success(bad)
        assert mgr.get_status().cooldown_proxies == 0
        assert mgr.get_status().healthy_proxies == 2
    finally:
        await mgr.stop_async()
        for rel in (cache_rel, state_rel):
            if exists(rel):
                delete(rel)
