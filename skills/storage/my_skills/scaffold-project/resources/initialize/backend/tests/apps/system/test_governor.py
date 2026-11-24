from __future__ import annotations
import asyncio
import pytest
from src.apps.system import (
    CpuTelemetry,
    GpuDeviceTelemetry,
    GpuTelemetry,
    HardwareTelemetrySnapshot,
    LoadLevel,
    RamTelemetry,
    TokenType,
    UserTier,
    WorkloadProfile,
)
from src.apps.system.helpers import (
    HardwareCircuitBreaker,
    HardwareProfiler,
    ResourceAllocator,
    ResourceGovernor,
)
from src.helpers import AppError


def _snap(
    cpu_pct: float = 10.0,
    ram_pct: float = 40.0,
    ram_avail_mb: int = 8192,
    total_ram_mb: int = 16384,
    temp_c: int = 45,
) -> HardwareTelemetrySnapshot:
    return HardwareTelemetrySnapshot(
        timestamp=1.0,
        cpu=CpuTelemetry(logical_cores=16, physical_cores=8, effective_cores=16, load_percent=cpu_pct),
        ram=RamTelemetry(
            total_bytes=total_ram_mb * 1024 * 1024,
            available_bytes=ram_avail_mb * 1024 * 1024,
            used_bytes=(total_ram_mb - ram_avail_mb) * 1024 * 1024,
            free_bytes=ram_avail_mb * 1024 * 1024,
            percent=ram_pct,
            process_rss_bytes=200 * 1024 * 1024,
        ),
        gpu=GpuTelemetry(
            device_id=0,
            name="NVIDIA GeForce RTX 3070 Ti",
            total_vram_bytes=8192 * 1024 * 1024,
            free_vram_bytes=2448 * 1024 * 1024,
            compute_capability="8.6",
            driver_version="610.88",
            cuda_available=True,
            nvenc_verified=True,
            nvenc_encoders=["h264_nvenc"],
            devices=[
                GpuDeviceTelemetry(
                    device_id=0,
                    name="NVIDIA GeForce RTX 3070 Ti",
                    total_vram_bytes=8192 * 1024 * 1024,
                    free_vram_bytes=2448 * 1024 * 1024,
                    used_vram_bytes=5744 * 1024 * 1024,
                    compute_capability="8.6",
                    driver_version="610.88",
                    temperature_c=temp_c,
                )
            ],
        ),
    )


@pytest.mark.asyncio
async def test_governor_honors_elevated_load_and_fifo_waiter_wakeup() -> None:
    current = {"snap": _snap(cpu_pct=78.0)}
    allocator = ResourceAllocator(max_encode_slots=2)
    allocator.register_profile(
        WorkloadProfile(
            name="render_test",
            token_type=TokenType.HYBRID.value,
            base_slots=2,
            gpu_capable=True,
            vram_reserve_mb=512,
            degradation_matrix={
                LoadLevel.NORMAL: 1.0,
                LoadLevel.ELEVATED: 0.5,
                LoadLevel.CRITICAL: 0.5,
                LoadLevel.EMERGENCY: 0.0,
            },
        )
    )
    gov = ResourceGovernor(telemetry_source=lambda: current["snap"], allocator=allocator)
    assert gov.get_load_level() == LoadLevel.ELEVATED

    p1 = await gov.acquire_resource_permit("render_test", "j1", user_tier=UserTier.PREMIUM, timeout=1.0)
    assert p1.gpu_enabled is True
    assert p1.hwaccel == "cuda"

    waiter_task = asyncio.create_task(
        gov.acquire_resource_permit("render_test", "j2", user_tier=UserTier.PREMIUM, timeout=2.0)
    )
    await asyncio.sleep(0.08)
    assert not waiter_task.done()

    gov.release_permit(p1.lease)  # type: ignore[arg-type]
    p2 = await waiter_task
    assert p2.job_id == "j2"
    gov.release_permit(p2.lease)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_governor_cancelled_waiter_does_not_block_next_waiter() -> None:
    snap = _snap(cpu_pct=10.0)
    alloc = ResourceAllocator(max_encode_slots=1)
    gov = ResourceGovernor(telemetry_source=lambda: snap, allocator=alloc)
    p1 = await gov.acquire_resource_permit("encode", "j1", user_tier=UserTier.PREMIUM, timeout=1.0)

    w_cancel = asyncio.create_task(gov.acquire_resource_permit("encode", "j_cancel", user_tier=UserTier.PREMIUM, timeout=2.0))
    w_next = asyncio.create_task(gov.acquire_resource_permit("encode", "j_next", user_tier=UserTier.PREMIUM, timeout=2.0))
    await asyncio.sleep(0.05)

    w_cancel.cancel()
    with pytest.raises(asyncio.CancelledError):
        await w_cancel

    gov.release_permit(p1.lease)  # type: ignore[arg-type]
    p2 = await w_next
    assert p2.job_id == "j_next"
    gov.release_permit(p2.lease)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_governor_gpu_downgrade_and_emergency_ram_starvation() -> None:
    hot_snap = _snap(cpu_pct=15.0, temp_c=88)
    gov_hot = ResourceGovernor(
        telemetry_source=lambda: hot_snap,
        allocator=ResourceAllocator(max_encode_slots=2),
        circuit_breaker=HardwareCircuitBreaker(),
    )
    p_cpu = await gov_hot.acquire_resource_permit("encode", "j_hot", user_tier=UserTier.PREMIUM, timeout=1.0)
    assert p_cpu.gpu_enabled is False
    assert p_cpu.hwaccel == "cpu"
    assert p_cpu.gpu_downgrade_reason is not None
    assert "temp=" in p_cpu.gpu_downgrade_reason
    gov_hot.release_permit(p_cpu.lease)  # type: ignore[arg-type]

    starved_snap = _snap(cpu_pct=96.0, ram_pct=96.0, ram_avail_mb=200)
    gov_starved = ResourceGovernor(telemetry_source=lambda: starved_snap, profiler=HardwareProfiler())
    with pytest.raises(AppError) as err_info:
        await gov_starved.acquire_resource_permit("encode", "j_oom", user_tier=UserTier.PREMIUM, timeout=1.0)
    assert err_info.value.status_code == 503


def test_governor_sync_permit_both_inside_and_outside_loop() -> None:
    snap = _snap(cpu_pct=10.0)
    gov = ResourceGovernor(telemetry_source=lambda: snap, allocator=ResourceAllocator(max_encode_slots=2))
    lease = gov.acquire_permit_sync("encode", "j_sync_1", timeout=2.0)
    assert lease.job_id == "j_sync_1"
    gov.release_permit(lease)

    async def inner() -> str:
        inner_lease = gov.acquire_permit_sync("encode", "j_sync_2", timeout=2.0)
        try:
            return inner_lease.job_id
        finally:
            gov.release_permit(inner_lease)

    assert asyncio.run(inner()) == "j_sync_2"
