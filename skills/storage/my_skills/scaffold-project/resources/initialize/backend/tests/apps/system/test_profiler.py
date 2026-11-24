from __future__ import annotations
import pytest
from src.apps.system import (
    CpuTelemetry,
    GpuDeviceTelemetry,
    GpuHealthState,
    GpuTelemetry,
    HardwareTelemetrySnapshot,
    LoadLevel,
    RamTelemetry,
)
from src.apps.system.helpers import HardwareCircuitBreaker, HardwareProfiler
from src.config import Settings


def _make_snapshot(
    cpu_pct: float = 10.0,
    ram_pct: float = 40.0,
    ram_avail_mb: int = 4096,
    gpu_enabled: bool = True,
    nvenc_verified: bool = True,
    free_vram_mb: int = 2400,
    total_vram_mb: int = 8192,
    temp_c: int = 48,
    gpu_util_pct: float = 10.0,
) -> HardwareTelemetrySnapshot:
    gpu: GpuTelemetry | None = None
    if gpu_enabled:
        gpu = GpuTelemetry(
            device_id=0,
            name="NVIDIA GeForce RTX 3070 Ti",
            total_vram_bytes=total_vram_mb * 1024 * 1024,
            free_vram_bytes=free_vram_mb * 1024 * 1024,
            compute_capability="8.6",
            driver_version="610.88",
            cuda_available=True,
            nvenc_verified=nvenc_verified,
            nvenc_encoders=["h264_nvenc"] if nvenc_verified else [],
            nvenc_failure_reason=None if nvenc_verified else "canary failed",
            devices=[
                GpuDeviceTelemetry(
                    device_id=0,
                    name="NVIDIA GeForce RTX 3070 Ti",
                    total_vram_bytes=total_vram_mb * 1024 * 1024,
                    free_vram_bytes=free_vram_mb * 1024 * 1024,
                    used_vram_bytes=max(0, total_vram_mb - free_vram_mb) * 1024 * 1024,
                    compute_capability="8.6",
                    driver_version="610.88",
                    temperature_c=temp_c,
                    gpu_util_percent=gpu_util_pct,
                )
            ],
        )
    total_b = 12000 * 1024 * 1024
    avail_b = ram_avail_mb * 1024 * 1024
    return HardwareTelemetrySnapshot(
        timestamp=1.0,
        cpu=CpuTelemetry(logical_cores=16, physical_cores=8, load_percent=cpu_pct),
        ram=RamTelemetry(
            total_bytes=total_b,
            available_bytes=avail_b,
            used_bytes=max(0, total_b - avail_b),
            free_bytes=avail_b,
            percent=ram_pct,
        ),
        gpu=gpu,
    )


def test_profiler_hysteresis_immediate_escalation_and_damped_recovery() -> None:
    profiler = HardwareProfiler()
    level, _ = profiler.evaluate_load_level(_make_snapshot(cpu_pct=15.0))
    assert level == LoadLevel.NORMAL

    level, reason = profiler.evaluate_load_level(_make_snapshot(cpu_pct=89.0))
    assert level == LoadLevel.CRITICAL
    assert "cpu=" in reason

    level, _ = profiler.evaluate_load_level(_make_snapshot(cpu_pct=85.0))
    assert level == LoadLevel.CRITICAL

    assert profiler.evaluate_load_level(_make_snapshot(cpu_pct=50.0))[0] == LoadLevel.CRITICAL
    assert profiler.evaluate_load_level(_make_snapshot(cpu_pct=50.0))[0] == LoadLevel.CRITICAL
    dropped, _ = profiler.evaluate_load_level(_make_snapshot(cpu_pct=50.0))
    assert dropped == LoadLevel.NORMAL


def test_profiler_gpu_health_states_and_non_mutating_circuit_check(monkeypatch: pytest.MonkeyPatch) -> None:
    profiler = HardwareProfiler()
    breaker = HardwareCircuitBreaker(failure_threshold=1, cooldown_period=0.05)

    assert profiler.evaluate_gpu_health(_make_snapshot(), breaker)[0] == GpuHealthState.HEALTHY
    assert profiler.evaluate_gpu_health(_make_snapshot(nvenc_verified=False), breaker)[0] == GpuHealthState.NVENC_FAILED
    assert profiler.evaluate_gpu_health(_make_snapshot(gpu_enabled=False), breaker)[0] == GpuHealthState.UNAVAILABLE
    assert profiler.evaluate_gpu_health(_make_snapshot(temp_c=88), breaker)[0] == GpuHealthState.THERMAL_THROTTLED
    assert profiler.evaluate_gpu_health(_make_snapshot(gpu_util_pct=92.0), breaker)[0] == GpuHealthState.UTIL_SATURATED
    assert profiler.evaluate_gpu_health(_make_snapshot(free_vram_mb=300), breaker)[0] == GpuHealthState.VRAM_PRESSURED
    assert profiler.evaluate_gpu_health(_make_snapshot(free_vram_mb=700, total_vram_mb=8192), breaker)[0] == GpuHealthState.VRAM_PRESSURED

    breaker.record_failure("h264_nvenc", "driver error")
    state, _ = profiler.evaluate_gpu_health(_make_snapshot(), breaker, encoder="h264_nvenc")
    assert state == GpuHealthState.CIRCUIT_OPEN
    details = breaker.get_circuit_details("h264_nvenc")
    assert details.half_open_in_flight is False

    monkeypatch.setattr(Settings, "SYSTEM_GPU_ENABLED", False)
    assert profiler.evaluate_gpu_health(_make_snapshot(), breaker)[0] == GpuHealthState.DISABLED
