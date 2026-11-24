import pytest
from src.apps.system import (
    CpuTelemetry,
    GpuBackend,
    GpuHealthState,
    GpuTelemetry,
    HardwareTelemetrySnapshot,
    LedgerCommitmentSnapshot,
    LoadLevel,
    RamTelemetry,
    ResourceLease,
    ResourcePermit,
    SystemResourceBudget,
    SystemStatusSnapshot,
    TokenType,
    WorkloadType,
)
from src.apps.system.helpers import HardwareValidator, ResourceValidator
from src.core.validators import (
    HardwareValidator as CoreHardwareValidator,
    ResourceValidator as CoreResourceValidator,
)


def test_core_validators_reexport_without_cycle() -> None:
    assert CoreHardwareValidator is HardwareValidator
    assert CoreResourceValidator is ResourceValidator


def test_hardware_telemetry_effective_cores() -> None:
    cpu = CpuTelemetry(logical_cores=16, physical_cores=8, load_percent=12.5)
    assert cpu.effective_cores == 16
    assert cpu.raw_load_percent == 0.0

    cgroup_cpu = CpuTelemetry(logical_cores=16, physical_cores=8, cgroup_quota_cores=4.0)
    assert cgroup_cpu.effective_cores == 4

    gpu_compat = GpuTelemetry(cuda_available=True, total_vram_bytes=8192 * 1024**2, free_vram_bytes=2048 * 1024**2)
    assert gpu_compat.is_available is True
    assert gpu_compat.is_usable is False
    assert gpu_compat.backend == GpuBackend.NVML
    assert len(gpu_compat.devices) == 1

    gpu_usable = gpu_compat.model_copy(update={"nvenc_verified": True, "nvenc_encoders": ["h264_nvenc"]})
    assert gpu_usable.is_usable is True


def test_validators_enforce_invariants_and_vram_token_rules() -> None:
    hw_val = HardwareValidator()
    cpu_bad_eff = CpuTelemetry(logical_cores=4, physical_cores=2, effective_cores=8)
    ok_cpu, errs_cpu = hw_val.validate_cpu(cpu_bad_eff)
    assert not ok_cpu and errs_cpu

    res_val = ResourceValidator()
    bad_vram_lease = ResourceLease(
        job_id="j1",
        workload_type="encode",
        token_type=TokenType.CPU.value,
        vram_bytes_allocated=512 * 1024**2,
    )
    ok_lease, errs_lease = res_val.validate_lease(bad_vram_lease)
    assert not ok_lease
    assert any("vram_bytes_allocated" in e for e in errs_lease)

    ok_hybrid = ResourceLease(
        job_id="j2",
        workload_type="encode",
        token_type=TokenType.HYBRID.value,
        gpu_device_id=0,
        vram_bytes_allocated=512 * 1024**2,
    )
    assert res_val.validate_lease(ok_hybrid)[0] is True


def test_resource_budget_and_status_snapshot_models() -> None:
    assert WorkloadType.EGRESS.value == "egress"
    permit = ResourcePermit(job_id="j1", workload_name="render", hwaccel="cuda", gpu_enabled=True, gpu_device_id=0)
    assert permit.hwaccel == "cuda"
    snap = SystemStatusSnapshot(
        timestamp=1.0,
        hardware=HardwareTelemetrySnapshot(
            timestamp=1.0,
            cpu=CpuTelemetry(logical_cores=16, physical_cores=8),
            ram=RamTelemetry(total_bytes=8 * 1024**3, available_bytes=4 * 1024**3, used_bytes=4 * 1024**3, free_bytes=4 * 1024**3),
        ),
        load_level=LoadLevel.NORMAL,
        gpu_health=GpuHealthState.HEALTHY,
        budget=SystemResourceBudget(
            effective_cores=16, usable_cpu_threads=14, total_ram_mb=8192,
            available_ram_mb=4096, external_used_ram_mb=2048, usable_ram_mb=5120,
        ),
        ledger=LedgerCommitmentSnapshot(),
    )
    assert snap.budget.usable_cpu_threads == 14
