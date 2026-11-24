from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
import threading
import time
from typing import AsyncGenerator, Optional
from src.config import EnvChanges, Settings, get_env_reloader, setup_logger
from .schema import (
    CircuitState,
    CpuTelemetry,
    GpuHealthState,
    HardwareTelemetrySnapshot,
    LedgerCommitmentSnapshot,
    LoadLevel,
    RamTelemetry,
    ResourceLease,
    ResourcePermit,
    SystemResourceBudget,
    SystemStatusSnapshot,
    ThreadBudgetDecision,
    TokenType,
    UserTier,
    WorkloadProfile,
    WorkloadType,
)
from .helpers import (
    HardwareCircuitBreaker,
    HardwareProbe,
    HardwareProfiler,
    HardwareValidator,
    LeaseTracker,
    ResourceAllocator,
    ResourceBudgetCalculator,
    ResourceGovernor,
    ResourceValidator,
    get_circuit_breaker,
)

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.manager")


async def _manager_sleep(interval: float) -> None:
    await asyncio.sleep(interval)


class SystemManager:
    _instance: Optional[SystemManager] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        circuit_breaker: Optional[HardwareCircuitBreaker] = None,
        probe: Optional[HardwareProbe] = None,
        governor: Optional[ResourceGovernor] = None,
        profiler: Optional[HardwareProfiler] = None,
        allocator: Optional[ResourceAllocator] = None,
        lease_tracker: Optional[LeaseTracker] = None,
        reaper_interval: Optional[float] = None,
        budget_calculator: Optional[ResourceBudgetCalculator] = None,
        validator: Optional[ResourceValidator] = None,
    ) -> None:
        self.circuit_breaker = circuit_breaker or get_circuit_breaker()
        self.probe = probe or HardwareProbe(circuit_breaker=self.circuit_breaker)
        self.profiler = profiler or HardwareProfiler()
        self.budget_calculator = budget_calculator or ResourceBudgetCalculator()
        self.allocator = allocator or ResourceAllocator()
        self.lease_tracker = lease_tracker or LeaseTracker()
        self.validator = validator or ResourceValidator()
        self.hardware_validator = HardwareValidator()
        self.governor = governor or ResourceGovernor(
            probe=self.probe,
            profiler=self.profiler,
            budget_calculator=self.budget_calculator,
            circuit_breaker=self.circuit_breaker,
            allocator=self.allocator,
            lease_tracker=self.lease_tracker,
            validator=self.validator,
        )
        self.reaper_interval: float = (
            reaper_interval if reaper_interval is not None else Settings.SYSTEM_REAPER_INTERVAL_SEC
        )
        self._running: bool = False
        self._reaper_task: Optional[asyncio.Task[None]] = None
        self._sampler_task: Optional[asyncio.Task[None]] = None
        self._lock = threading.Lock()
        self._banner_logged: bool = False
        self._last_load_level: Optional[LoadLevel] = None
        self._last_gpu_health: Optional[GpuHealthState] = None
        self._last_heartbeat_at: float = 0.0
        get_env_reloader().register(
            name="system",
            env_path_fn=lambda: Settings.SYSTEM_CONFIG_FILE,
            prefixes=("SYSTEM_",),
            on_change=self._on_env_changed,
        )

    @classmethod
    def get_instance(cls) -> SystemManager:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            inst = cls._instance
            cls._instance = None
        if inst is not None:
            inst.stop()
            inst.probe.shutdown()

    def _spawn_background_tasks(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            if self._reaper_task is None or self._reaper_task.done():
                self._reaper_task = loop.create_task(self._reaper_loop())
            if self._sampler_task is None or self._sampler_task.done():
                self._sampler_task = loop.create_task(self._sampler_loop())
        except RuntimeError:
            self._reaper_task = None
            self._sampler_task = None

    def _evaluate_state(
        self, snapshot: HardwareTelemetrySnapshot
    ) -> tuple[LoadLevel, str, GpuHealthState, str, SystemResourceBudget]:
        return self.governor.evaluate_state(snapshot)

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._sync_config_state()
            self._spawn_background_tasks()
        logger.info("SystemManager started")

    async def start_async(self) -> HardwareTelemetrySnapshot:
        with self._lock:
            already_running = self._running
            self._running = True
            self._sync_config_state()
        snapshot = await self.probe.sample(force_refresh=True, warmup=True)
        level, _, gpu_health, gpu_reason, budget = self._evaluate_state(snapshot)
        with self._lock:
            self._last_load_level = level
            self._last_gpu_health = gpu_health
            self._last_heartbeat_at = time.monotonic()
            should_banner = not self._banner_logged
            self._banner_logged = True
            self._spawn_background_tasks()
        if should_banner or not already_running:
            self._log_startup_banner(snapshot, level, gpu_health, gpu_reason, budget)
        logger.info("SystemManager started")
        return snapshot

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False
            if self._reaper_task is not None and not self._reaper_task.done():
                self._reaper_task.cancel()
            self._reaper_task = None
            if self._sampler_task is not None and not self._sampler_task.done():
                self._sampler_task.cancel()
            self._sampler_task = None
        self.probe.shutdown()
        logger.info("SystemManager stopped")

    async def stop_async(self) -> None:
        with self._lock:
            tasks = [t for t in (self._reaper_task, self._sampler_task) if t is not None and not t.done()]
        self.stop()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError as err:
                logger.debug(f"SystemManager background task cancelled on shutdown: {err}")

    def _sync_config_state(self) -> None:
        get_env_reloader().sync_entry("system")

    async def _on_env_changed(self, _changes: EnvChanges) -> None:
        self.allocator.sync_from_settings()

    async def _check_config_reload(self) -> list[str]:
        changes = await get_env_reloader().check_entry_async("system")
        return sorted(changes.keys())

    def _log_startup_cpu_ram(self, snapshot: HardwareTelemetrySnapshot, budget: SystemResourceBudget) -> None:
        cgroup_val = (
            f"{snapshot.cpu.cgroup_quota_cores:.2f}"
            if snapshot.cpu.cgroup_quota_cores is not None
            else "none"
        )
        logger.info(
            f"system.startup.cpu physical={snapshot.cpu.physical_cores} logical={snapshot.cpu.logical_cores} "
            f"effective={snapshot.cpu.effective_cores} cgroup={cgroup_val} load={snapshot.cpu.load_percent:.1f}% "
            f"load_1m={snapshot.cpu.load_1m:.2f} usable_threads={budget.usable_cpu_threads} "
            f"(cap={Settings.SYSTEM_MAX_CPU_USAGE_PERCENT:.0f}% reserved={Settings.SYSTEM_RESERVED_CPU_CORES})"
        )
        rss_mb = snapshot.ram.process_rss_bytes // (1024 * 1024)
        swap_used_mb = snapshot.ram.swap_used_bytes // (1024 * 1024)
        swap_total_mb = snapshot.ram.swap_total_bytes // (1024 * 1024)
        logger.info(
            f"system.startup.ram total={budget.total_ram_mb}MB avail={budget.available_ram_mb}MB "
            f"used={snapshot.ram.percent:.1f}% process_rss={rss_mb}MB swap={swap_used_mb}/{swap_total_mb}MB "
            f"usable_budget={budget.usable_ram_mb}MB (cap={Settings.SYSTEM_MAX_RAM_USAGE_PERCENT:.0f}% "
            f"floor={Settings.SYSTEM_MIN_FREE_RAM_MB}MB)"
        )

    def _log_startup_gpu(
        self,
        snapshot: HardwareTelemetrySnapshot,
        gpu_health: GpuHealthState,
        gpu_reason: str,
        budget: SystemResourceBudget,
    ) -> None:
        gpu = snapshot.gpu
        if gpu is not None and gpu.cuda_available and gpu.total_vram_bytes > 0:
            primary = gpu.devices[0] if gpu.devices else None
            used_b = primary.used_vram_bytes if primary is not None else max(0, gpu.total_vram_bytes - gpu.free_vram_bytes)
            used_mb = used_b // (1024 * 1024)
            total_mb = gpu.total_vram_bytes // (1024 * 1024)
            free_mb = gpu.free_vram_bytes // (1024 * 1024)
            if gpu.nvenc_verified:
                util = primary.gpu_util_percent if primary is not None else 0.0
                temp = primary.temperature_c if primary is not None else 0
                encoders_str = ",".join(gpu.nvenc_encoders) if gpu.nvenc_encoders else "none"
                logger.info(
                    f"system.startup.gpu backend={gpu.backend.value} count={gpu.device_count} dev={gpu.device_id} "
                    f"name=\"{gpu.name}\" cc={gpu.compute_capability} driver={gpu.driver_version} "
                    f"vram={used_mb}/{total_mb}MB free={free_mb}MB util={util:.0f}% temp={temp}C "
                    f"nvenc=ready encoders={encoders_str} max_sessions={budget.max_gpu_sessions} "
                    f"vram_budget={budget.usable_vram_mb}MB health={gpu_health.value}"
                )
            else:
                reason = gpu.nvenc_failure_reason or gpu_reason
                logger.warning(
                    f"system.startup.gpu backend={gpu.backend.value} count={gpu.device_count} dev={gpu.device_id} "
                    f"name=\"{gpu.name}\" cc={gpu.compute_capability} driver={gpu.driver_version} "
                    f"vram={used_mb}/{total_mb}MB free={free_mb}MB nvenc=FAILED reason=\"{reason}\" fallback=cpu_only"
                )
            return
        if gpu is not None and gpu.vaapi_available:
            primary = gpu.devices[0] if gpu.devices else None
            used_b = primary.used_vram_bytes if primary is not None else max(0, gpu.total_vram_bytes - gpu.free_vram_bytes)
            used_mb = used_b // (1024 * 1024)
            total_mb = gpu.total_vram_bytes // (1024 * 1024)
            free_mb = gpu.free_vram_bytes // (1024 * 1024)
            util = primary.gpu_util_percent if primary is not None else 0.0
            temp = primary.temperature_c if primary is not None else 0
            logger.info(
                f"system.startup.gpu backend={gpu.backend.value} count={gpu.device_count} dev={gpu.device_id} "
                f"name=\"{gpu.name}\" vram={used_mb}/{total_mb}MB free={free_mb}MB util={util:.0f}% temp={temp}C "
                f"vaapi=ready max_sessions={budget.max_gpu_sessions} vram_budget={budget.usable_vram_mb}MB health={gpu_health.value}"
            )
            return
        vaapi_ok = gpu.vaapi_available if gpu is not None else False
        backend = gpu.backend.value if gpu is not None else "none"
        reason = (gpu.unavailable_reason if gpu is not None else None) or gpu_reason
        logger.info(
            f"system.startup.gpu backend={backend} gpu=unavailable reason=\"{reason}\" "
            f"vaapi={str(vaapi_ok).lower()} mode=cpu_only"
        )

    def _log_startup_policy(self, level: LoadLevel) -> None:
        caps = self.allocator.get_all_capacities(level)
        caps_str = ",".join(f"{k}:{caps[k]}" for k in sorted(caps))
        tiers_str = (
            f"guest:{Settings.SYSTEM_TIER_GUEST_CPU_RATIO:.2f}x/{Settings.SYSTEM_TIER_GUEST_RAM_MB}MB,"
            f"registered:{Settings.SYSTEM_TIER_REGISTERED_CPU_RATIO:.2f}x/{Settings.SYSTEM_TIER_REGISTERED_RAM_MB}MB,"
            f"premium:{Settings.SYSTEM_TIER_PREMIUM_CPU_RATIO:.2f}x/{Settings.SYSTEM_TIER_PREMIUM_RAM_MB}MB,"
            f"gpu_tiers={Settings.SYSTEM_GPU_ALLOWED_TIERS}"
        )
        logger.info(
            f"system.startup.policy load_level={level.value} capacities={{{caps_str}}} "
            f"tiers={{{tiers_str}}} config={Settings.SYSTEM_CONFIG_FILE} "
            f"poll={Settings.SYSTEM_TELEMETRY_POLL_INTERVAL_SEC:.1f}s "
            f"heartbeat={Settings.SYSTEM_HEARTBEAT_INTERVAL_SEC:.1f}s reaper={self.reaper_interval:.1f}s"
        )

    def _log_startup_banner(
        self,
        snapshot: HardwareTelemetrySnapshot,
        level: LoadLevel,
        gpu_health: GpuHealthState,
        gpu_reason: str,
        budget: SystemResourceBudget,
    ) -> None:
        self._log_startup_cpu_ram(snapshot, budget)
        self._log_startup_gpu(snapshot, gpu_health, gpu_reason, budget)
        self._log_startup_policy(level)

    def _format_gpu_heartbeat_tag(self, snapshot: HardwareTelemetrySnapshot, gpu_health: GpuHealthState) -> str:
        gpu = snapshot.gpu
        if gpu is None or not gpu.is_available:
            return f"none(state={gpu_health.value})"
        primary = gpu.devices[0] if gpu.devices else None
        util = primary.gpu_util_percent if primary is not None else 0.0
        temp = primary.temperature_c if primary is not None else 0
        used_b = primary.used_vram_bytes if primary is not None else max(0, gpu.total_vram_bytes - gpu.free_vram_bytes)
        used_mb = used_b // (1024 * 1024)
        total_mb = gpu.total_vram_bytes // (1024 * 1024)
        free_mb = gpu.free_vram_bytes // (1024 * 1024)
        return (
            f"dev{gpu.device_id}(backend={gpu.backend.value} util={util:.0f}% temp={temp}C "
            f"vram={used_mb}/{total_mb}MB free={free_mb}MB state={gpu_health.value})"
        )

    def _emit_transitions_and_heartbeat(
        self,
        snapshot: HardwareTelemetrySnapshot,
        level: LoadLevel,
        load_reason: str,
        gpu_health: GpuHealthState,
        gpu_reason: str,
        budget: SystemResourceBudget,
    ) -> None:
        ledger = self.lease_tracker.get_commitment_snapshot()
        now_mono = time.monotonic()

        if self._last_load_level is not None and level != self._last_load_level:
            log_fn = logger.warning if level.severity_rank > self._last_load_level.severity_rank else logger.info
            log_fn(
                f"system.load.transition from={self._last_load_level.value} to={level.value} "
                f"reason=\"{load_reason}\" cpu={snapshot.cpu.load_percent:.1f}% "
                f"ram={snapshot.ram.percent:.1f}%(avail={budget.available_ram_mb}MB) "
                f"active_leases={ledger.active_leases}"
            )
        self._last_load_level = level

        if self._last_gpu_health is not None and gpu_health != self._last_gpu_health:
            log_fn = logger.info if gpu_health == GpuHealthState.HEALTHY else logger.warning
            gpu = snapshot.gpu
            free_vram_mb = (gpu.free_vram_bytes // (1024 * 1024)) if gpu is not None else 0
            primary = gpu.devices[0] if (gpu is not None and gpu.devices) else None
            temp = primary.temperature_c if primary is not None else 0
            util = primary.gpu_util_percent if primary is not None else 0.0
            log_fn(
                f"system.gpu.transition from={self._last_gpu_health.value} to={gpu_health.value} "
                f"reason=\"{gpu_reason}\" free_vram={free_vram_mb}MB temp={temp}C util={util:.0f}%"
            )
        self._last_gpu_health = gpu_health

        if (now_mono - self._last_heartbeat_at) >= Settings.SYSTEM_HEARTBEAT_INTERVAL_SEC:
            self._last_heartbeat_at = now_mono
            gpu_str = self._format_gpu_heartbeat_tag(snapshot, gpu_health)
            logger.info(
                f"system.heartbeat level={level.value} cpu={snapshot.cpu.load_percent:.1f}% "
                f"ram={snapshot.ram.percent:.1f}%(avail={budget.available_ram_mb}MB) gpu={gpu_str} "
                f"committed={{leases:{ledger.active_leases} threads:{ledger.committed_threads}/{budget.usable_cpu_threads} "
                f"ram:{ledger.committed_ram_mb}/{budget.usable_ram_mb}MB "
                f"gpu_sess:{ledger.committed_gpu_sessions}/{budget.max_gpu_sessions} "
                f"vram:{ledger.committed_vram_mb}/{budget.usable_vram_mb}MB}}"
            )

    async def _sampler_step(self) -> None:
        await self._check_config_reload()
        snapshot = await self.probe.sample(force_refresh=True, warmup=not self._banner_logged)
        level, load_reason, gpu_health, gpu_reason, budget = self._evaluate_state(snapshot)
        if not self._banner_logged:
            self._banner_logged = True
            self._last_load_level = level
            self._last_gpu_health = gpu_health
            self._last_heartbeat_at = time.monotonic()
            self._log_startup_banner(snapshot, level, gpu_health, gpu_reason, budget)
            return
        self._emit_transitions_and_heartbeat(snapshot, level, load_reason, gpu_health, gpu_reason, budget)

    async def _sampler_loop(self) -> None:
        while self._running:
            try:
                await self._sampler_step()
                await _manager_sleep(Settings.SYSTEM_TELEMETRY_POLL_INTERVAL_SEC)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in SystemManager sampler loop: {e}")
                await _manager_sleep(Settings.SYSTEM_TELEMETRY_POLL_INTERVAL_SEC)

    async def _reaper_loop(self) -> None:
        while self._running:
            try:
                await _manager_sleep(self.reaper_interval)
                self.reap_expired_leases()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in SystemManager reaper loop: {e}")

    def get_snapshot(self, force_refresh: bool = False) -> HardwareTelemetrySnapshot:
        return self.probe.run(force_refresh=force_refresh)

    async def get_snapshot_async(self, force_refresh: bool = False) -> HardwareTelemetrySnapshot:
        return await self.probe.sample(force_refresh=force_refresh)

    def get_load_level(self) -> LoadLevel:
        return self.governor.get_load_level()

    def get_stress_level(self, snapshot: Optional[HardwareTelemetrySnapshot] = None) -> str:
        current_snapshot = snapshot if snapshot is not None else self.get_snapshot()
        return self.profiler.evaluate_stress(current_snapshot)

    def is_cpu_saturated(self, cpu: Optional[CpuTelemetry] = None) -> bool:
        if cpu is not None:
            return self.profiler.is_cpu_saturated(cpu)
        return self.profiler.is_cpu_saturated(self.get_snapshot().cpu)

    def is_memory_pressured(self, ram: Optional[RamTelemetry] = None) -> bool:
        if ram is not None:
            return self.profiler.is_memory_pressured(ram)
        return self.profiler.is_memory_pressured(self.get_snapshot().ram)

    def get_gpu_health(
        self,
        snapshot: Optional[HardwareTelemetrySnapshot] = None,
        encoder: str = "h264_nvenc",
    ) -> tuple[GpuHealthState, str]:
        snap = snapshot if snapshot is not None else self.get_snapshot()
        return self.profiler.evaluate_gpu_health(snap, self.circuit_breaker, encoder)

    def get_budget(self, snapshot: Optional[HardwareTelemetrySnapshot] = None) -> SystemResourceBudget:
        snap = snapshot if snapshot is not None else self.get_snapshot()
        _, _, _, _, budget = self._evaluate_state(snap)
        return budget

    def get_ledger_snapshot(self) -> LedgerCommitmentSnapshot:
        return self.lease_tracker.get_commitment_snapshot()

    def _build_status_snapshot(self, snapshot: HardwareTelemetrySnapshot) -> SystemStatusSnapshot:
        level, _, gpu_health, _, budget = self._evaluate_state(snapshot)
        ledger = self.lease_tracker.get_commitment_snapshot()
        return SystemStatusSnapshot(
            timestamp=snapshot.timestamp,
            hardware=snapshot,
            load_level=level,
            gpu_health=gpu_health,
            budget=budget,
            ledger=ledger,
            workload_capacities=self.allocator.get_all_capacities(level),
            encoder_circuits=self.circuit_breaker.list_states(),
            active_limits={
                "SYSTEM_MAX_CPU_USAGE_PERCENT": Settings.SYSTEM_MAX_CPU_USAGE_PERCENT,
                "SYSTEM_RESERVED_CPU_CORES": Settings.SYSTEM_RESERVED_CPU_CORES,
                "SYSTEM_MAX_RAM_USAGE_PERCENT": Settings.SYSTEM_MAX_RAM_USAGE_PERCENT,
                "SYSTEM_MIN_FREE_RAM_MB": Settings.SYSTEM_MIN_FREE_RAM_MB,
                "SYSTEM_GPU_ENABLED": Settings.SYSTEM_GPU_ENABLED,
                "SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT": Settings.SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT,
                "SYSTEM_GPU_MIN_FREE_VRAM_MB": Settings.SYSTEM_GPU_MIN_FREE_VRAM_MB,
                "SYSTEM_GPU_MAX_TEMP_C": Settings.SYSTEM_GPU_MAX_TEMP_C,
                "SYSTEM_GPU_MAX_UTIL_PERCENT": Settings.SYSTEM_GPU_MAX_UTIL_PERCENT,
                "SYSTEM_GPU_MAX_NVENC_SESSIONS": Settings.SYSTEM_GPU_MAX_NVENC_SESSIONS,
                "SYSTEM_GPU_ALLOWED_TIERS": Settings.SYSTEM_GPU_ALLOWED_TIERS,
            },
        )

    def get_status_snapshot(self, force_refresh: bool = False) -> SystemStatusSnapshot:
        return self._build_status_snapshot(self.get_snapshot(force_refresh=force_refresh))

    async def get_status_snapshot_async(self, force_refresh: bool = False) -> SystemStatusSnapshot:
        snapshot = await self.get_snapshot_async(force_refresh=force_refresh)
        return self._build_status_snapshot(snapshot)

    def can_execute_encoder(self, encoder: str) -> bool:
        return self.circuit_breaker.can_execute(encoder)

    def record_encoder_success(self, encoder: str) -> None:
        self.circuit_breaker.record_success(encoder)

    def record_encoder_failure(self, encoder: str, reason: str = "") -> None:
        self.circuit_breaker.record_failure(encoder, reason=reason)

    def notify_hardware_anomaly(self, encoder: str, reason: str) -> None:
        logger.warning(f"system.hardware.anomaly encoder={encoder} reason=\"{reason}\"")
        self.record_encoder_failure(encoder, reason=reason)

    def get_encoder_circuit_state(self, encoder: str) -> CircuitState:
        return self.circuit_breaker.get_state(encoder)

    def reset_encoder_circuit(self, encoder: str) -> None:
        self.circuit_breaker.reset(encoder)

    def reset_all_circuits(self) -> None:
        self.circuit_breaker.reset_all()

    def get_capacity(self, workload_type: str, load_level: Optional[LoadLevel] = None) -> int:
        level = load_level if load_level is not None else self.get_load_level()
        return self.allocator.get_capacity(workload_type, level)

    def get_active_count(self, workload_type: str) -> int:
        return self.allocator.get_active(workload_type)

    def can_admit_workload(self, workload_type: str, load_level: Optional[LoadLevel] = None) -> bool:
        level = load_level if load_level is not None else self.get_load_level()
        return self.allocator.can_admit(workload_type, level)

    def reserve_workload_slot(self, workload_type: str) -> None:
        self.allocator.allocate(workload_type)

    def release_workload_slot(self, workload_type: str) -> None:
        self.allocator.release(workload_type)

    def attach_job_lease_metadata(self, job_id: str, key: str, value: str) -> bool:
        lease = self.lease_tracker.get_lease_by_job(job_id)
        if lease is None:
            return False
        lease.metadata[key] = value
        return True

    def get_optimal_encode_concurrency(self) -> int:
        return self.governor.get_optimal_encode_concurrency()

    async def acquire_permit(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> ResourceLease:
        return await self.governor.acquire_permit(
            workload_type, job_id, user_tier=user_tier, timeout=timeout, ttl=ttl,
        )

    def release_permit(self, lease: ResourceLease) -> None:
        self.governor.release_permit(lease)

    def calculate_user_permit(
        self,
        workload_type: str,
        job_id: str = "",
        user_tier: UserTier = UserTier.GUEST,
        lease: Optional[ResourceLease] = None,
    ) -> ResourcePermit:
        norm_workload = workload_type.strip().lower()
        snapshot = self.get_snapshot()
        level, _, gpu_health, gpu_reason, budget = self._evaluate_state(snapshot)
        ledger = self.lease_tracker.get_commitment_snapshot()
        profile = self.allocator.get_profile(norm_workload)
        slot_capacity = max(1, profile.calculate_capacity(level))
        decision, _ = self.budget_calculator.calculate_permit(
            profile=profile,
            user_tier=user_tier,
            load_level=level,
            snapshot=snapshot,
            gpu_health=gpu_health,
            gpu_health_reason=gpu_reason,
            budget=budget,
            ledger=ledger,
            unmaterialized_vram_mb=0,
            slot_capacity=slot_capacity,
            encoder_available=not self.circuit_breaker.is_tripped("h264_nvenc"),
        )
        if decision is None:
            return ResourcePermit(
                job_id=job_id,
                user_tier=user_tier,
                workload_type=self.budget_calculator.resolve_workload_enum(norm_workload, profile.token_type),
                workload_name=norm_workload,
                allocated_threads=1,
                allocated_memory_mb=min(self.budget_calculator.tier_ram_mb(user_tier), profile.min_ram_mb),
                gpu_enabled=False,
                hwaccel="cpu",
                preferred_encoder="libx264",
                lease=lease,
            )
        return ResourcePermit(
            job_id=job_id,
            user_tier=user_tier,
            workload_type=decision.workload_enum,
            workload_name=norm_workload,
            allocated_threads=decision.allocated_threads,
            allocated_memory_mb=decision.allocated_memory_mb,
            gpu_enabled=decision.gpu_enabled,
            gpu_device_id=decision.gpu_device_id,
            hwaccel=decision.hwaccel,
            preferred_encoder=decision.preferred_encoder,
            allocated_vram_mb=decision.allocated_vram_mb,
            gpu_downgrade_reason=decision.gpu_downgrade_reason,
            lease=lease,
        )

    async def acquire_resource_permit(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> ResourcePermit:
        return await self.governor.acquire_resource_permit(
            workload_type=workload_type,
            job_id=job_id,
            user_tier=user_tier,
            timeout=timeout,
            ttl=ttl,
        )

    def release_resource_permit(self, permit: ResourcePermit) -> None:
        permit.release()
        if permit.lease is not None:
            self.release_permit(permit.lease)

    def release_permit_by_job_id(self, job_id: str) -> bool:
        lease = self.lease_tracker.get_lease_by_job(job_id)
        if lease is not None:
            self.release_permit(lease)
            return True
        return False

    def acquire_permit_sync(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> ResourceLease:
        return self.governor.acquire_permit_sync(
            workload_type, job_id, user_tier=user_tier, timeout=timeout, ttl=ttl,
        )

    @asynccontextmanager
    async def lease(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> AsyncGenerator[ResourceLease, None]:
        async with self.governor.lease(workload_type, job_id, user_tier=user_tier, timeout=timeout, ttl=ttl) as active_lease:
            yield active_lease

    def reap_expired_leases(self) -> int:
        return self.governor.reap_expired_leases()

    def register_workload(self, profile: WorkloadProfile) -> None:
        self.allocator.register_profile(profile)

    def get_workload_profile(self, workload_type: str) -> WorkloadProfile:
        return self.allocator.get_profile(workload_type)

    def has_workload_profile(self, workload_type: str) -> bool:
        return self.allocator.has_profile(workload_type)

    def get_all_workload_capacities(self, load_level: Optional[LoadLevel] = None) -> dict[str, int]:
        level = load_level if load_level is not None else self.get_load_level()
        return self.allocator.get_all_capacities(level)

    def calculate_thread_budget(
        self,
        workload: str = "encode",
        logical_cores: Optional[int] = None,
        max_threads_cap: int = 16,
        hw_accel: bool = False,
    ) -> ThreadBudgetDecision:
        snapshot = self.get_snapshot()
        level, _, _, _, budget = self._evaluate_state(snapshot)
        host_cores = max(1, logical_cores if logical_cores is not None else snapshot.cpu.logical_cores)
        effective_cores = min(host_cores, budget.usable_cpu_threads)
        workload_norm = workload.strip().lower()
        active = max(1, self.get_active_count(workload_norm))
        profile = self.allocator.get_profile(workload_norm)
        if hw_accel:
            allocated = min(Settings.SYSTEM_GPU_ENCODE_CPU_THREADS, profile.max_thread_cap, max_threads_cap, effective_cores)
        else:
            slot_budget = max(1, effective_cores // active)
            profile_threads = profile.calculate_threads(effective_cores, level)
            allocated = min(profile_threads, slot_budget, max_threads_cap)
        allocated = max(1, allocated)
        return ThreadBudgetDecision(
            workload=workload_norm,
            load_level=level,
            logical_cores=host_cores,
            effective_cores=effective_cores,
            active_jobs=active,
            hw_accel=hw_accel,
            allocated_threads=allocated,
        )

    def get_thread_args(
        self,
        workload: str = "encode",
        logical_cores: Optional[int] = None,
        max_threads_cap: int = 16,
        hw_accel: bool = False,
    ) -> list[str]:
        decision = self.calculate_thread_budget(
            workload=workload,
            logical_cores=logical_cores,
            max_threads_cap=max_threads_cap,
            hw_accel=hw_accel,
        )
        return ["-threads", str(decision.allocated_threads)]


def get_system_manager() -> SystemManager:
    return SystemManager.get_instance()
