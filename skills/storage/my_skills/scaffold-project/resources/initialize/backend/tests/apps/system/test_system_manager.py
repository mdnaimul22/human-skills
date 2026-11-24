from __future__ import annotations
import asyncio
import os
import time
import uuid
import pytest
from src.apps.system import (
    CircuitState,
    LoadLevel,
    ResourcePermit,
    TokenType,
    UserTier,
    WorkloadProfile,
)
from src.apps.system import SystemManager, get_system_manager
from src.config import Settings, delete, read_text, write_text


@pytest.fixture(autouse=True)
def clean_system_manager() -> None:
    SystemManager.reset_instance()
    yield
    SystemManager.reset_instance()


def test_system_manager_singleton_lifecycle() -> None:
    sm1 = get_system_manager()
    sm2 = SystemManager.get_instance()
    assert sm1 is sm2
    SystemManager.reset_instance()
    sm3 = get_system_manager()
    assert sm3 is not sm1


@pytest.mark.asyncio
async def test_system_manager_start_stop() -> None:
    sm = get_system_manager()
    sm.reaper_interval = 0.05
    sm.start()
    assert sm._running is True
    assert sm._reaper_task is not None
    await asyncio.sleep(0.06)
    sm.stop()
    assert sm._running is False
    assert sm._reaper_task is None


def test_system_manager_telemetry_and_stress() -> None:
    sm = get_system_manager()
    snapshot = sm.get_snapshot()
    assert snapshot.cpu.logical_cores >= 1
    assert snapshot.ram.total_bytes > 0

    load_level = sm.get_load_level()
    assert load_level in (LoadLevel.NORMAL, LoadLevel.ELEVATED, LoadLevel.CRITICAL, LoadLevel.EMERGENCY)

    stress = sm.get_stress_level(snapshot)
    assert stress in ("normal", "elevated", "critical")

    saturated = sm.is_cpu_saturated(snapshot.cpu)
    assert saturated in (True, False)

    pressured = sm.is_memory_pressured(snapshot.ram)
    assert pressured in (True, False)


@pytest.mark.asyncio
async def test_system_manager_snapshot_async() -> None:
    sm = get_system_manager()
    snapshot = await sm.get_snapshot_async(force_refresh=True)
    assert snapshot.cpu.logical_cores >= 1


def test_system_manager_circuit_breaker_flow() -> None:
    sm = get_system_manager()
    encoder = "test_nvenc"
    sm.reset_encoder_circuit(encoder)

    assert sm.can_execute_encoder(encoder) is True
    assert sm.get_encoder_circuit_state(encoder) == CircuitState.CLOSED

    for _ in range(3):
        sm.record_encoder_failure(encoder, reason="simulated driver crash")

    assert sm.get_encoder_circuit_state(encoder) == CircuitState.OPEN
    assert sm.can_execute_encoder(encoder) is False

    sm.reset_encoder_circuit(encoder)
    assert sm.get_encoder_circuit_state(encoder) == CircuitState.CLOSED
    assert sm.can_execute_encoder(encoder) is True


@pytest.mark.asyncio
async def test_system_manager_lease_context_manager() -> None:
    sm = get_system_manager()
    job_id = "job_test_cm"

    initial_active = sm.get_active_count("encode")

    async with sm.lease("encode", job_id, timeout=5.0) as lease:
        assert lease.job_id == job_id
        assert lease.workload_type == "encode"
        assert lease.is_active is True
        assert sm.get_active_count("encode") == initial_active + 1

    assert sm.get_active_count("encode") == initial_active


def test_system_manager_sync_permit_acquisition() -> None:
    sm = get_system_manager()
    job_id = "job_test_sync"

    lease = sm.acquire_permit_sync("download", job_id, timeout=5.0)
    try:
        assert lease.job_id == job_id
        assert sm.get_active_count("download") >= 1
    finally:
        sm.release_permit(lease)


def test_system_manager_reap_expired_leases() -> None:
    sm = get_system_manager()
    lease = sm.lease_tracker.create_lease("encode", "job_exp", ttl=0.01)
    time.sleep(0.02)
    reaped = sm.reap_expired_leases()
    assert reaped >= 1


def test_system_manager_thread_budget() -> None:
    sm = get_system_manager()

    decision_encode = sm.calculate_thread_budget("encode")
    assert decision_encode.allocated_threads >= 1
    assert decision_encode.logical_cores >= 1

    args_encode = sm.get_thread_args("encode")
    assert args_encode[0] == "-threads"
    assert int(args_encode[1]) >= 1

    decision_audio = sm.calculate_thread_budget("audio")
    assert decision_audio.allocated_threads <= 2

    decision_probe = sm.calculate_thread_budget("probe")
    assert decision_probe.allocated_threads <= 2


@pytest.mark.asyncio
async def test_system_manager_dynamic_workload_lifecycle() -> None:
    sm = get_system_manager()
    profile = WorkloadProfile(
        name="custom_smart_crop",
        token_type=TokenType.GPU.value,
        base_slots=3,
        max_thread_cap=4,
        degradation_matrix={
            LoadLevel.NORMAL: 1.0,
            LoadLevel.ELEVATED: 0.5,
            LoadLevel.CRITICAL: 0.25,
            LoadLevel.EMERGENCY: 0.0,
        },
    )
    sm.register_workload(profile)
    assert sm.has_workload_profile("custom_smart_crop") is True
    assert sm.get_capacity("custom_smart_crop", LoadLevel.NORMAL) == 3
    assert sm.get_capacity("custom_smart_crop", LoadLevel.EMERGENCY) == 0

    all_caps = sm.get_all_workload_capacities(LoadLevel.NORMAL)
    assert "custom_smart_crop" in all_caps
    assert all_caps["custom_smart_crop"] == 3

    decision = sm.calculate_thread_budget("custom_smart_crop", max_threads_cap=16)
    assert decision.allocated_threads <= 4

    async with sm.lease("custom_smart_crop", "job_crop_99", timeout=5.0) as lease:
        assert lease.workload_type == "custom_smart_crop"
        assert sm.get_active_count("custom_smart_crop") == 1
    assert sm.get_active_count("custom_smart_crop") == 0


@pytest.mark.asyncio
async def test_system_manager_user_tier_permit_allocation() -> None:
    sm = get_system_manager()
    guest_permit = await sm.acquire_resource_permit("download", "job_guest", user_tier=UserTier.GUEST, timeout=5.0)
    assert guest_permit.user_tier == UserTier.GUEST
    assert guest_permit.allocated_threads >= 1
    assert guest_permit.allocated_memory_mb == 256
    assert guest_permit.gpu_enabled is False
    assert sm.get_active_count("download") == 1

    registered_permit = await sm.acquire_resource_permit("download", "job_reg", user_tier=UserTier.REGISTERED, timeout=5.0)
    assert registered_permit.user_tier == UserTier.REGISTERED
    assert registered_permit.allocated_threads >= guest_permit.allocated_threads
    assert registered_permit.allocated_memory_mb == 512
    assert sm.get_active_count("download") == 2

    sm.release_resource_permit(guest_permit)
    sm.release_resource_permit(registered_permit)
    assert guest_permit.released is True
    assert registered_permit.released is True
    assert sm.get_active_count("download") == 0


@pytest.mark.asyncio
async def test_system_manager_start_async_banner_status_and_config_reload() -> None:
    sm = get_system_manager()
    snap = await sm.start_async()
    try:
        assert snap.cpu.logical_cores >= 1
        status = await sm.get_status_snapshot_async(force_refresh=False)
        assert status.budget.usable_cpu_threads >= 1
        assert "encode" in status.workload_capacities

        log_path = f"{Settings.LOG_DIR}/system.log"
        log_text = read_text(log_path)
        for marker in ("system.startup.cpu", "system.startup.ram", "system.startup.gpu", "system.startup.policy"):
            assert marker in log_text

        sm.record_encoder_failure("test_enc", "err")
        sm.reset_all_circuits()
        assert sm.get_encoder_circuit_state("test_enc") == CircuitState.CLOSED

        rel_cfg = f"tmp/test_tmp/sys_mgr_cfg_{os.getpid()}_{uuid.uuid4().hex[:6]}.env"
        orig_cfg = Settings.SYSTEM_CONFIG_FILE
        orig_cap = Settings.SYSTEM_MAX_CPU_USAGE_PERCENT
        orig_env = os.environ.get("SYSTEM_MAX_CPU_USAGE_PERCENT")
        try:
            Settings.SYSTEM_CONFIG_FILE = rel_cfg
            sm._sync_config_state()
            write_text(rel_cfg, "SYSTEM_MAX_CPU_USAGE_PERCENT=82.0\n")
            changed = await sm._check_config_reload()
            assert "SYSTEM_MAX_CPU_USAGE_PERCENT" in changed
            assert Settings.SYSTEM_MAX_CPU_USAGE_PERCENT == 82.0
        finally:
            Settings.SYSTEM_CONFIG_FILE = orig_cfg
            Settings.SYSTEM_MAX_CPU_USAGE_PERCENT = orig_cap
            if orig_env is None:
                os.environ.pop("SYSTEM_MAX_CPU_USAGE_PERCENT", None)
            else:
                os.environ["SYSTEM_MAX_CPU_USAGE_PERCENT"] = orig_env
            delete(rel_cfg)

        sm.reserve_workload_slot("egress")
        assert sm.get_active_count("egress") == 1
        sm.release_workload_slot("egress")
        assert sm.get_active_count("egress") == 0
    finally:
        await sm.stop_async()
