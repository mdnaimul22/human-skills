from __future__ import annotations
import asyncio
import sys
import pytest
from src.apps.system import GpuBackend
from src.apps.system.helpers import HardwareProbe


@pytest.mark.asyncio
async def test_live_hardware_probe_sample_warmup_and_fingerprint() -> None:
    probe = HardwareProbe(cache_ttl=2.0)
    try:
        snap = await probe.sample(force_refresh=True, warmup=True)
        assert "torch" not in sys.modules
        assert snap.cpu.logical_cores >= 1
        assert snap.cpu.physical_cores >= 1
        assert snap.cpu.effective_cores >= 1
        assert snap.ram.total_bytes > 0
        assert snap.ram.process_rss_bytes > 0
        assert len(snap.fingerprint) == 16
        assert snap.gpu is not None
        assert snap.gpu.backend == GpuBackend.NVML
        assert snap.gpu.nvenc_verified is True

        snap2 = await probe.sample(force_refresh=False)
        assert snap2.timestamp == snap.timestamp
    finally:
        probe.shutdown()


def test_hardware_probe_ewma_smoothing_and_cgroup_clamping(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = HardwareProbe(cache_ttl=2.0)
    try:
        readings = iter([80.0, 20.0])
        monkeypatch.setattr("src.apps.system.helpers.probe.psutil.cpu_percent", lambda interval=None: next(readings))
        monkeypatch.setattr("src.apps.system.helpers.probe.sys_exists", lambda p: p == "/sys/fs/cgroup/cpu.max")
        monkeypatch.setattr("src.apps.system.helpers.probe.sys_read_text", lambda _p: "400000 100000")

        c1 = probe._sample_cpu_sync()
        assert c1.raw_load_percent == 80.0
        assert c1.load_percent == 80.0
        assert c1.cgroup_quota_cores == pytest.approx(4.0)
        assert c1.effective_cores <= 4

        c2 = probe._sample_cpu_sync()
        assert c2.raw_load_percent == 20.0
        assert c2.load_percent == pytest.approx(0.4 * 20.0 + 0.6 * 80.0, abs=0.05)
    finally:
        probe.shutdown()


@pytest.mark.asyncio
async def test_hardware_probe_coalesces_concurrent_samples(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = HardwareProbe(cache_ttl=5.0)
    call_count = 0
    orig_ram = probe._sample_ram_sync

    def tracked_ram():
        nonlocal call_count
        call_count += 1
        return orig_ram()

    monkeypatch.setattr(probe, "_sample_ram_sync", tracked_ram)
    try:
        s1, s2, s3 = await asyncio.gather(
            probe.sample(force_refresh=True),
            probe.sample(force_refresh=True),
            probe.sample(force_refresh=True),
        )
        assert s1.fingerprint == s2.fingerprint == s3.fingerprint
        assert call_count >= 1
    finally:
        probe.shutdown()
