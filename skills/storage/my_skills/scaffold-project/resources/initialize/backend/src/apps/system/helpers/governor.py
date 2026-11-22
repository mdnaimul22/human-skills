from __future__ import annotations
import asyncio
from collections import defaultdict, deque
import concurrent.futures
from contextlib import asynccontextmanager
import threading
import time
from typing import AsyncGenerator, Callable, Optional
from src.config import Settings, setup_logger
from src.helpers import AppError, ValidationError
from ..schema import (
    GpuHealthState,
    HardwareTelemetrySnapshot,
    LoadLevel,
    ResourceLease,
    ResourcePermit,
    SystemResourceBudget,
    UserTier,
)
from .allocator import ResourceAllocator
from .budget import PermitAllocationDecision, ResourceBudgetCalculator
from .circuit_breaker import HardwareCircuitBreaker, get_circuit_breaker
from .lease_tracker import LeaseTracker
from .probe import HardwareProbe
from .profiler import HardwareProfiler
from .validator import ResourceValidator

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.governor")


class ResourceGovernor:
    _instance: Optional[ResourceGovernor] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        telemetry_source: Optional[Callable[[], HardwareTelemetrySnapshot]] = None,
        max_encode_slots: Optional[int] = None,
        max_download_slots: Optional[int] = None,
        allocator: Optional[ResourceAllocator] = None,
        lease_tracker: Optional[LeaseTracker] = None,
        validator: Optional[ResourceValidator] = None,
        probe: Optional[HardwareProbe] = None,
        profiler: Optional[HardwareProfiler] = None,
        budget_calculator: Optional[ResourceBudgetCalculator] = None,
        circuit_breaker: Optional[HardwareCircuitBreaker] = None,
    ) -> None:
        self._telemetry_source = telemetry_source
        self.max_encode_slots = max_encode_slots
        self.max_download_slots = max_download_slots
        self.probe = probe or HardwareProbe.get_instance()
        self.profiler = profiler or HardwareProfiler()
        self.budget_calculator = budget_calculator or ResourceBudgetCalculator()
        self.circuit_breaker = circuit_breaker or get_circuit_breaker()
        self.allocator = allocator or ResourceAllocator(
            max_encode_slots=max_encode_slots,
            max_download_slots=max_download_slots,
        )
        self.lease_tracker = lease_tracker or LeaseTracker()
        self.validator = validator or ResourceValidator()
        self._thread_lock = threading.Lock()
        self._waiters: dict[str, deque[tuple[asyncio.AbstractEventLoop, asyncio.Event]]] = defaultdict(deque)

    @classmethod
    def get_instance(cls) -> ResourceGovernor:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            cls._instance = None

    def _sample_telemetry(self) -> HardwareTelemetrySnapshot:
        if self._telemetry_source is not None:
            return self._telemetry_source()
        return self.probe.run(force_refresh=False)

    async def _sample_telemetry_async(self) -> HardwareTelemetrySnapshot:
        if self._telemetry_source is not None:
            return await asyncio.to_thread(self._telemetry_source)
        return await self.probe.sample(force_refresh=False)

    def _wake_waiters(self, workload_type: Optional[str] = None) -> None:
        to_notify: list[tuple[asyncio.AbstractEventLoop, asyncio.Event]] = []
        with self._thread_lock:
            for queue in self._waiters.values():
                if queue:
                    to_notify.extend(queue)
        for loop, event in to_notify:
            try:
                if not loop.is_closed():
                    loop.call_soon_threadsafe(event.set)
            except RuntimeError as err:
                logger.debug(f"Waiter notification skipped for closed loop: {err}")

    def evaluate_state(
        self, snapshot: HardwareTelemetrySnapshot
    ) -> tuple[LoadLevel, str, GpuHealthState, str, SystemResourceBudget]:
        level, load_reason = self.profiler.evaluate_load_level(snapshot)
        gpu_health, gpu_reason = self.profiler.evaluate_gpu_health(snapshot, self.circuit_breaker, "h264_nvenc")
        budget = self.budget_calculator.compute_usable_budget(snapshot, gpu_health)
        return level, load_reason, gpu_health, gpu_reason, budget

    def get_load_level(self) -> LoadLevel:
        try:
            snapshot = self._sample_telemetry()
        except Exception as e:
            logger.error(f"Failed to query telemetry for load level: {e}")
            return LoadLevel.ELEVATED
        level, _ = self.profiler.evaluate_load_level(snapshot)
        return level

    def get_optimal_encode_concurrency(self) -> int:
        try:
            snapshot = self._sample_telemetry()
        except Exception as e:
            logger.error(f"Failed to query telemetry for optimal concurrency: {e}")
            return 1
        level, _, _, _, budget = self.evaluate_state(snapshot)
        total_ram_gb = snapshot.ram.total_bytes / (1024**3)
        if budget.gpu_usable and total_ram_gb >= 8.0 and budget.effective_cores >= 8:
            base = max(1, min(6, budget.max_gpu_sessions))
        else:
            base = max(1, budget.usable_cpu_threads // 4)
        if level == LoadLevel.NORMAL:
            return min(base, self.max_encode_slots) if self.max_encode_slots is not None else base
        if level == LoadLevel.ELEVATED:
            return max(1, int(base * 0.75))
        return 1

    def _check_ram_starvation(
        self,
        job_id: str,
        workload_type: str,
        snapshot: HardwareTelemetrySnapshot,
        level: LoadLevel,
    ) -> None:
        if level != LoadLevel.EMERGENCY:
            return
        avail_mb = snapshot.ram.available_bytes // (1024 * 1024)
        floor_mb = Settings.SYSTEM_RAM_EMERGENCY_FREE_MB
        if avail_mb < floor_mb:
            logger.warning(
                f"permit.denied job={job_id} workload={workload_type} "
                f"reason=ram_starvation(avail={avail_mb}MB<{floor_mb}MB) level={level.value}"
            )
            raise AppError("Server memory depleted; unable to admit permit", status_code=503)

    def _log_permit_granted(
        self,
        job_id: str,
        workload_type: str,
        user_tier: UserTier,
        level: LoadLevel,
        decision: PermitAllocationDecision,
        budget: SystemResourceBudget,
    ) -> None:
        post_ledger = self.lease_tracker.get_commitment_snapshot()
        if decision.gpu_downgrade_reason:
            logger.warning(
                f"permit.gpu_downgraded job={job_id} workload={workload_type} tier={user_tier.value} "
                f"reason={decision.gpu_downgrade_reason} fallback=cpu(threads={decision.allocated_threads})"
            )
        gpu_tag = (
            f"cuda:{decision.gpu_device_id}({decision.preferred_encoder},vram={decision.allocated_vram_mb}MB)"
            if decision.gpu_enabled
            else "cpu"
        )
        logger.info(
            f"permit.acquired job={job_id} workload={workload_type} tier={user_tier.value} "
            f"threads={decision.allocated_threads} ram={decision.allocated_memory_mb}MB "
            f"gpu={gpu_tag} level={level.value} "
            f"ledger={{threads:{post_ledger.committed_threads}/{budget.usable_cpu_threads} "
            f"ram:{post_ledger.committed_ram_mb}/{budget.usable_ram_mb}MB "
            f"gpu:{post_ledger.committed_gpu_sessions}/{budget.max_gpu_sessions} "
            f"vram:{post_ledger.committed_vram_mb}/{budget.usable_vram_mb}MB}}"
        )

    def _try_reserve_or_enqueue(
        self,
        norm_type: str,
        job_id: str,
        user_tier: UserTier,
        level: LoadLevel,
        snapshot: HardwareTelemetrySnapshot,
        gpu_health: GpuHealthState,
        gpu_reason: str,
        budget: SystemResourceBudget,
        ttl: Optional[float],
        deadline: float,
        loop: asyncio.AbstractEventLoop,
    ) -> tuple[Optional[ResourcePermit], Optional[asyncio.Event], int, str]:
        encoder_avail = not self.circuit_breaker.is_tripped("h264_nvenc")
        with self._thread_lock:
            profile = self.allocator.get_profile(norm_type)
            slot_capacity = profile.calculate_capacity(level)
            active_slots = self.allocator.get_active(norm_type)

            if active_slots < slot_capacity:
                ledger = self.lease_tracker.get_commitment_snapshot()
                unmat_vram = self.lease_tracker.get_unmaterialized_vram_mb(
                    Settings.SYSTEM_TELEMETRY_POLL_INTERVAL_SEC * 2.0
                )
                decision, deny_reason = self.budget_calculator.calculate_permit(
                    profile=profile,
                    user_tier=user_tier,
                    load_level=level,
                    snapshot=snapshot,
                    gpu_health=gpu_health,
                    gpu_health_reason=gpu_reason,
                    budget=budget,
                    ledger=ledger,
                    unmaterialized_vram_mb=unmat_vram,
                    slot_capacity=slot_capacity,
                    encoder_available=encoder_avail,
                )
                if decision is not None:
                    eff_ttl = ttl if (ttl is not None and ttl > 0.0) else profile.default_ttl
                    self.allocator.allocate(norm_type)
                    lease = self.lease_tracker.create_lease(
                        workload_type=norm_type,
                        job_id=job_id,
                        ttl=eff_ttl,
                        token_type=decision.token_type,
                        cpu_cores_allocated=decision.allocated_threads,
                        memory_bytes_allocated=decision.allocated_memory_mb * 1024 * 1024,
                        gpu_device_id=decision.gpu_device_id,
                        vram_bytes_allocated=decision.allocated_vram_mb * 1024 * 1024,
                    )
                    try:
                        lease.metadata["loop_key"] = str(id(loop))
                        self.validator.assert_valid_lease(lease)
                    except Exception:
                        self.lease_tracker.release_lease(lease)
                        self.allocator.release(norm_type)
                        raise
                    permit = ResourcePermit(
                        job_id=job_id,
                        user_tier=user_tier,
                        workload_type=decision.workload_enum,
                        workload_name=norm_type,
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
                    self._log_permit_granted(job_id, norm_type, user_tier, level, decision, budget)
                    return permit, None, 0, ""
                reason = deny_reason or "budget_exhausted"
            else:
                reason = (
                    f"workload_disabled_under_load({level.value})"
                    if slot_capacity == 0
                    else f"slot_full({active_slots}/{slot_capacity})"
                )

            wait_event: Optional[asyncio.Event] = None
            queue_pos = 0
            if (deadline - time.monotonic()) > 0.0:
                wait_event = asyncio.Event()
                self._waiters[norm_type].append((loop, wait_event))
                queue_pos = len(self._waiters[norm_type])
            return None, wait_event, queue_pos, reason

    def _remove_waiter(self, norm_type: str, wait_event: asyncio.Event) -> None:
        with self._thread_lock:
            q = self._waiters.get(norm_type)
            if q is not None:
                for i, pair in enumerate(q):
                    if pair[1] is wait_event:
                        del q[i]
                        break

    async def _await_waiter_step(self, norm_type: str, wait_event: Optional[asyncio.Event], remaining: float) -> None:
        timed_out = False
        try:
            if wait_event is not None:
                await asyncio.wait_for(wait_event.wait(), timeout=min(remaining, 0.25))
            else:
                await asyncio.sleep(min(remaining, 0.05))
        except asyncio.TimeoutError:
            timed_out = True
        finally:
            if wait_event is not None:
                self._remove_waiter(norm_type, wait_event)
        _ = timed_out

    async def acquire_resource_permit(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> ResourcePermit:
        if not job_id or not str(job_id).strip():
            raise ValidationError("job_id must not be empty")
        if timeout <= 0.0:
            raise ValidationError("timeout must be greater than zero")

        norm_type = workload_type.strip().lower()
        started = time.monotonic()
        deadline = started + timeout
        wait_logged = False
        loop = asyncio.get_running_loop()

        while True:
            snapshot = await self._sample_telemetry_async()
            level, _, gpu_health, gpu_reason, budget = self.evaluate_state(snapshot)
            self._check_ram_starvation(job_id, norm_type, snapshot, level)

            permit, wait_event, queue_pos, deny_reason = self._try_reserve_or_enqueue(
                norm_type, job_id, user_tier, level, snapshot, gpu_health, gpu_reason, budget, ttl, deadline, loop,
            )
            if permit is not None:
                return permit

            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                if wait_event is not None:
                    self._remove_waiter(norm_type, wait_event)
                logger.warning(
                    f"permit.denied job={job_id} workload={norm_type} tier={user_tier.value} "
                    f"reason=timeout({timeout:.1f}s,{deny_reason}) level={level.value}"
                )
                raise asyncio.TimeoutError(
                    f"Permit acquisition timed out for job={job_id} workload={norm_type} ({deny_reason})"
                )

            if not wait_logged and (time.monotonic() - started) >= 1.0:
                wait_logged = True
                logger.info(
                    f"permit.waiting job={job_id} workload={norm_type} reason={deny_reason} "
                    f"queue_pos={queue_pos} level={level.value}"
                )

            await self._await_waiter_step(norm_type, wait_event, remaining)

    async def acquire_permit(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> ResourceLease:
        permit = await self.acquire_resource_permit(
            workload_type=workload_type,
            job_id=job_id,
            user_tier=user_tier,
            timeout=timeout,
            ttl=ttl,
        )
        if permit.lease is None:
            raise AppError("Acquired resource permit missing lease token", status_code=500)
        return permit.lease

    def release_permit(self, lease: ResourceLease) -> None:
        if lease is None or lease.released:
            return
        with self._thread_lock:
            released = self.lease_tracker.release_lease(lease)
            if released:
                self.allocator.release(lease.workload_type)
            snapshot = self.lease_tracker.get_commitment_snapshot()
        if released:
            self._wake_waiters(lease.workload_type)
            held_sec = max(0.0, time.time() - lease.allocated_at)
            logger.info(
                f"permit.released job={lease.job_id} workload={lease.workload_type} "
                f"lease={lease.lease_id} held={held_sec:.2f}s "
                f"ledger={{leases:{snapshot.active_leases} threads:{snapshot.committed_threads} "
                f"ram:{snapshot.committed_ram_mb}MB gpu_sess:{snapshot.committed_gpu_sessions}}}"
            )

    def reap_expired_leases(self) -> int:
        now = time.time()
        with self._thread_lock:
            expired = self.lease_tracker.reap_expired(now=now)
            for lease in expired:
                self.allocator.release(lease.workload_type)
        if expired:
            for lease in expired:
                overdue = max(0.0, now - lease.expires_at)
                ram_mb = lease.memory_bytes_allocated // (1024 * 1024)
                vram_mb = lease.vram_bytes_allocated // (1024 * 1024)
                logger.warning(
                    f"lease.reaped job={lease.job_id} workload={lease.workload_type} "
                    f"lease={lease.lease_id} overdue={overdue:.1f}s "
                    f"reclaimed={{threads:{lease.cpu_cores_allocated} ram:{ram_mb}MB "
                    f"gpu:{lease.gpu_device_id} vram:{vram_mb}MB}}"
                )
            self._wake_waiters()
        return len(expired)

    @asynccontextmanager
    async def lease(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> AsyncGenerator[ResourceLease, None]:
        permit = await self.acquire_permit(workload_type, job_id, user_tier=user_tier, timeout=timeout, ttl=ttl)
        try:
            yield permit
        finally:
            self.release_permit(permit)

    def acquire_permit_sync(
        self,
        workload_type: str,
        job_id: str,
        user_tier: UserTier = UserTier.GUEST,
        timeout: float = 30.0,
        ttl: Optional[float] = None,
    ) -> ResourceLease:
        def _invoke() -> ResourceLease:
            return asyncio.run(
                self.acquire_permit(workload_type, job_id, user_tier=user_tier, timeout=timeout, ttl=ttl)
            )

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    return executor.submit(_invoke).result()
        except RuntimeError as e:
            logger.debug(f"Event loop check for sync permit: {e}")
        return _invoke()
