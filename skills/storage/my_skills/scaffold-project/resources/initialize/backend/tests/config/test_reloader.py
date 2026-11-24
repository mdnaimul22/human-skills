from __future__ import annotations
import os
import uuid
import pytest
from src.config import EnvChanges, EnvHotReloader, Settings, delete, exists, write_text


def test_env_hot_reloader_sync_callback_and_rollback() -> None:
    rel_cfg = f"tmp/test_tmp/reloader_{os.getpid()}_{uuid.uuid4().hex[:6]}.env"
    orig_cpu = Settings.SYSTEM_MAX_CPU_USAGE_PERCENT
    orig_env = os.environ.get("SYSTEM_MAX_CPU_USAGE_PERCENT")
    seen: list[EnvChanges] = []
    reloader = EnvHotReloader()
    try:
        write_text(rel_cfg, f"SYSTEM_MAX_CPU_USAGE_PERCENT={orig_cpu}\n")
        reloader.register(
            name="sys",
            env_path_fn=lambda: rel_cfg,
            prefixes=("SYSTEM_",),
            on_change=lambda ch: seen.append(ch),
        )
        assert reloader.check_entry_sync("sys") == {}

        write_text(rel_cfg, "SYSTEM_MAX_CPU_USAGE_PERCENT=81.5\n")
        changes = reloader.check_entry_sync("sys")
        assert changes == {"SYSTEM_MAX_CPU_USAGE_PERCENT": (orig_cpu, 81.5)}
        assert Settings.SYSTEM_MAX_CPU_USAGE_PERCENT == 81.5
        assert len(seen) == 1

        assert reloader.check_entry_sync("sys") == {}

        write_text(rel_cfg, "SYSTEM_MAX_CPU_USAGE_PERCENT=999.0\n")
        assert reloader.check_entry_sync("sys") == {}
        assert Settings.SYSTEM_MAX_CPU_USAGE_PERCENT == 81.5
    finally:
        Settings.SYSTEM_MAX_CPU_USAGE_PERCENT = orig_cpu
        if orig_env is None:
            os.environ.pop("SYSTEM_MAX_CPU_USAGE_PERCENT", None)
        else:
            os.environ["SYSTEM_MAX_CPU_USAGE_PERCENT"] = orig_env
        if exists(rel_cfg):
            delete(rel_cfg)


@pytest.mark.asyncio
async def test_env_hot_reloader_async_callback_and_check_all() -> None:
    rel_cfg = f"tmp/test_tmp/reloader_async_{os.getpid()}_{uuid.uuid4().hex[:6]}.env"
    orig_provider = Settings.TUNNEL_PROVIDER
    orig_env = os.environ.get("TUNNEL_PROVIDER")
    seen: list[EnvChanges] = []
    reloader = EnvHotReloader()

    async def _on_async_change(changes: EnvChanges) -> None:
        seen.append(changes)

    try:
        write_text(rel_cfg, f"TUNNEL_PROVIDER={orig_provider}\n")
        reloader.register(
            name="tunnel",
            env_path_fn=lambda: rel_cfg,
            prefixes=("TUNNEL_",),
            exact_keys=("TUNNEL",),
            on_change=_on_async_change,
        )
        write_text(rel_cfg, "TUNNEL_PROVIDER=tailscale\n")
        all_changes = await reloader.check_all_async()
        assert "tunnel" in all_changes
        assert Settings.TUNNEL_PROVIDER == "tailscale"
        assert len(seen) == 1
    finally:
        Settings.TUNNEL_PROVIDER = orig_provider
        if orig_env is None:
            os.environ.pop("TUNNEL_PROVIDER", None)
        else:
            os.environ["TUNNEL_PROVIDER"] = orig_env
        if exists(rel_cfg):
            delete(rel_cfg)
