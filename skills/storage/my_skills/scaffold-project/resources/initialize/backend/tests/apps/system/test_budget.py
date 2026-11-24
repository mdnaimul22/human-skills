from __future__ import annotations
import pytest
from src.apps.system import (
    CpuTelemetry,
    GpuDeviceTelemetry,
    GpuHealthState,
    GpuTelemetry,
    HardwareTelemetrySnapshot,
    LedgerCommitmentSnapshot,
    LoadLevel,
    RamTelemetry,
    TokenType,
    UserTier,
    WorkloadProfile,
    WorkloadType,
)
from src.apps.system.helpers import ResourceBudgetCalculator
from src.config import Settings


def _make_hw(
    cores: int = 16,
    total_ram_mb: int = 12000,
    avail_ram_mb: int = 8000,
    process_rss_mb: int = 200,
    with_gpu: bool = True,
    total_vram_mb: int = 8192,
    free_vram_mb: int = 2448,
) -> HardwareTelemetrySnapshot:
    gpu = None
    if with_gpu:
        gpu = GpuTelemetry(
            device_id=0,
            name="NVIDIA GeForce RTX 3070 Ti",
            total_vram_bytes=total_vram_mb * 1024 * 1024,
            free_vram_bytes=free_vram_mb * 1024 * 1024,
            compute_capability="8.6",
            driver_version="610.88",
            cuda_available=True,
            nvenc_verified=True,
            nvenc_encoders=["h264_nvenc"],
            devices=[
                GpuDeviceTelemetry(
                    device_id=0,
                    name="NVIDIA GeForce RTX 3070 Ti",
                    total_vram_bytes=total_vram_mb * 1024 * 1024,
                    free_vram_bytes=free_vram_mb * 1024 * 1024,
                    used_vram_bytes=(total_vram_mb - free_vram_mb) * 1024 * 1024,
                    compute_capability="8.6",
                    driver_version="610.88",
                )
            ],
        )
    return HardwareTelemetrySnapshot(
        timestamp=10.0,
        cpu=CpuTelemetry(logical_cores=cores, physical_cores=max(1, cores // 2), effective_cores=cores, load_percent=10.0),
        ram=RamTelemetry(
            total_bytes=total_ram_mb * 1024 * 1024,
            available_bytes=avail_ram_mb * 1024 * 1024,
            used_bytes=(total_ram_mb - avail_ram_mb) * 1024 * 1024,
            free_bytes=avail_ram_mb * 1024 * 1024,
            percent=round(((total_ram_mb - avail_ram_mb) / total_ram_mb) * 100.0, 1),
            process_rss_bytes=process_rss_mb * 1024 * 1024,
        ),
        gpu=gpu,
    )


def test_budget_90_percent_ceilings_and_external_ram_exclusion() -> None:
    calc = ResourceBudgetCalculator()
    snap = _make_hw(cores=16, total_ram_mb=12000, avail_ram_mb=6200, process_rss_mb=200, with_gpu=True, total_vram_mb=8192, free_vram_mb=2448)
    budget = calc.compute_usable_budget(snap, GpuHealthState.HEALTHY)

    expected_threads = min(int(16 * (Settings.SYSTEM_MAX_CPU_USAGE_PERCENT / 100.0)), 16 - Settings.SYSTEM_RESERVED_CPU_CORES)
    assert budget.usable_cpu_threads == max(1, expected_threads)
    assert budget.external_used_ram_mb == 5600
    assert budget.usable_ram_mb == 12000 - 5600 - Settings.SYSTEM_MIN_FREE_RAM_MB
    assert budget.gpu_usable is True
    assert budget.vram_headroom_mb == 2448 - Settings.SYSTEM_GPU_MIN_FREE_VRAM_MB
    assert budget.max_gpu_sessions == 3


def test_budget_anti_oversubscription_fair_share_and_gpu_fallback() -> None:
    calc = ResourceBudgetCalculator()
    snap = _make_hw(cores=16, total_ram_mb=16384, avail_ram_mb=12000, process_rss_mb=200, with_gpu=True, total_vram_mb=8192, free_vram_mb=2448)
    budget = calc.compute_usable_budget(snap, GpuHealthState.HEALTHY)
    encode_profile = WorkloadProfile(
        name="encode",
        token_type=TokenType.HYBRID.value,
        base_slots=3,
        max_thread_cap=8,
        min_threads=1,
        min_ram_mb=256,
        max_ram_mb=2048,
        gpu_capable=True,
        vram_reserve_mb=512,
    )

    decision_prem, deny = calc.calculate_permit(
        profile=encode_profile,
        user_tier=UserTier.PREMIUM,
        load_level=LoadLevel.NORMAL,
        snapshot=snap,
        gpu_health=GpuHealthState.HEALTHY,
        gpu_health_reason="healthy",
        budget=budget,
        ledger=LedgerCommitmentSnapshot(),
        unmaterialized_vram_mb=0,
        slot_capacity=3,
    )
    assert deny is None and decision_prem is not None
    assert decision_prem.gpu_enabled is True
    assert decision_prem.hwaccel == "cuda"
    assert decision_prem.preferred_encoder == "h264_nvenc"
    assert decision_prem.allocated_threads == Settings.SYSTEM_GPU_ENCODE_CPU_THREADS
    assert decision_prem.allocated_vram_mb == 512
    assert decision_prem.workload_enum == WorkloadType.ENCODE

    decision_guest, deny_g = calc.calculate_permit(
        profile=encode_profile,
        user_tier=UserTier.GUEST,
        load_level=LoadLevel.NORMAL,
        snapshot=snap,
        gpu_health=GpuHealthState.HEALTHY,
        gpu_health_reason="healthy",
        budget=budget,
        ledger=LedgerCommitmentSnapshot(),
        unmaterialized_vram_mb=0,
        slot_capacity=3,
    )
    assert deny_g is None and decision_guest is not None
    assert decision_guest.gpu_enabled is False
    assert decision_guest.hwaccel == "cpu"
    assert decision_guest.allocated_memory_mb == Settings.SYSTEM_TIER_GUEST_RAM_MB

    budget_hot = calc.compute_usable_budget(snap, GpuHealthState.THERMAL_THROTTLED)
    decision_cpu_fb, _ = calc.calculate_permit(
        profile=encode_profile,
        user_tier=UserTier.PREMIUM,
        load_level=LoadLevel.NORMAL,
        snapshot=snap,
        gpu_health=GpuHealthState.THERMAL_THROTTLED,
        gpu_health_reason="temp=88C>=83C",
        budget=budget_hot,
        ledger=LedgerCommitmentSnapshot(),
        unmaterialized_vram_mb=0,
        slot_capacity=3,
    )
    assert decision_cpu_fb is not None
    assert decision_cpu_fb.gpu_enabled is False
    assert decision_cpu_fb.hwaccel == "cpu"
    assert decision_cpu_fb.gpu_downgrade_reason is not None

    ml_profile = WorkloadProfile(
        name="ml",
        token_type=TokenType.GPU.value,
        base_slots=2,
        gpu_capable=True,
        is_exclusive_gpu=True,
        vram_reserve_mb=1536,
    )
    ml_dec, ml_deny = calc.calculate_permit(
        profile=ml_profile,
        user_tier=UserTier.PREMIUM,
        load_level=LoadLevel.NORMAL,
        snapshot=snap,
        gpu_health=GpuHealthState.THERMAL_THROTTLED,
        gpu_health_reason="temp=88C>=83C",
        budget=budget_hot,
        ledger=LedgerCommitmentSnapshot(),
        unmaterialized_vram_mb=0,
        slot_capacity=2,
    )
    assert ml_dec is None and ml_deny is not None


def test_budget_rejects_when_cpu_or_ram_ledger_full() -> None:
    calc = ResourceBudgetCalculator()
    snap = _make_hw(cores=8, total_ram_mb=8192, avail_ram_mb=4096, process_rss_mb=100, with_gpu=False)
    budget = calc.compute_usable_budget(snap, GpuHealthState.UNAVAILABLE)
    cpu_profile = WorkloadProfile(name="encode", token_type=TokenType.CPU.value, base_slots=2, min_threads=1, min_ram_mb=256)

    dec_cpu_full, reason_cpu = calc.calculate_permit(
        profile=cpu_profile,
        user_tier=UserTier.REGISTERED,
        load_level=LoadLevel.NORMAL,
        snapshot=snap,
        gpu_health=GpuHealthState.UNAVAILABLE,
        gpu_health_reason="none",
        budget=budget,
        ledger=LedgerCommitmentSnapshot(committed_threads=budget.usable_cpu_threads),
        unmaterialized_vram_mb=0,
        slot_capacity=2,
    )
    assert dec_cpu_full is None and "cpu_budget_exhausted" in (reason_cpu or "")

    dec_ram_full, reason_ram = calc.calculate_permit(
        profile=cpu_profile,
        user_tier=UserTier.REGISTERED,
        load_level=LoadLevel.NORMAL,
        snapshot=snap,
        gpu_health=GpuHealthState.UNAVAILABLE,
        gpu_health_reason="none",
        budget=budget,
        ledger=LedgerCommitmentSnapshot(committed_ram_mb=budget.usable_ram_mb),
        unmaterialized_vram_mb=0,
        slot_capacity=2,
    )
    assert dec_ram_full is None and "ram_budget_exhausted" in (reason_ram or "")
