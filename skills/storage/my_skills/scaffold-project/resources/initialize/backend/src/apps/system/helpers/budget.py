from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from src.config import Settings
from ..schema import (
    GpuHealthState,
    HardwareTelemetrySnapshot,
    LedgerCommitmentSnapshot,
    LoadLevel,
    SystemResourceBudget,
    TokenType,
    UserTier,
    WorkloadProfile,
    WorkloadType,
)


class PermitAllocationDecision(BaseModel):
    allocated_threads: int = Field(ge=1)
    allocated_memory_mb: int = Field(ge=1)
    gpu_enabled: bool = False
    gpu_device_id: int = -1
    allocated_vram_mb: int = Field(default=0, ge=0)
    hwaccel: str = "cpu"
    preferred_encoder: str = "libx264"
    token_type: str = TokenType.CPU.value
    workload_enum: WorkloadType = WorkloadType.ENCODE
    gpu_downgrade_reason: Optional[str] = None


class ResourceBudgetCalculator:
    @staticmethod
    def resolve_workload_enum(workload_name: str, token_type: str) -> WorkloadType:
        norm = workload_name.strip().lower()
        if norm == "video":
            return WorkloadType.ENCODE
        for member in WorkloadType:
            if member.value == norm:
                return member
        if token_type in (TokenType.GPU.value, TokenType.HYBRID.value):
            return WorkloadType.ENCODE
        return WorkloadType.DOWNLOAD

    @staticmethod
    def tier_cpu_ratio(user_tier: UserTier) -> float:
        ratios: dict[UserTier, float] = {
            UserTier.GUEST: Settings.SYSTEM_TIER_GUEST_CPU_RATIO,
            UserTier.REGISTERED: Settings.SYSTEM_TIER_REGISTERED_CPU_RATIO,
            UserTier.PREMIUM: Settings.SYSTEM_TIER_PREMIUM_CPU_RATIO,
        }
        return ratios.get(user_tier, Settings.SYSTEM_TIER_GUEST_CPU_RATIO)

    @staticmethod
    def tier_ram_mb(user_tier: UserTier) -> int:
        caps: dict[UserTier, int] = {
            UserTier.GUEST: Settings.SYSTEM_TIER_GUEST_RAM_MB,
            UserTier.REGISTERED: Settings.SYSTEM_TIER_REGISTERED_RAM_MB,
            UserTier.PREMIUM: Settings.SYSTEM_TIER_PREMIUM_RAM_MB,
        }
        return caps.get(user_tier, Settings.SYSTEM_TIER_GUEST_RAM_MB)

    @staticmethod
    def gpu_allowed_tiers() -> set[str]:
        return {t.strip().lower() for t in Settings.SYSTEM_GPU_ALLOWED_TIERS.split(",") if t.strip()}

    def compute_usable_budget(
        self,
        snapshot: HardwareTelemetrySnapshot,
        gpu_health: GpuHealthState,
    ) -> SystemResourceBudget:
        eff_cores = max(1, snapshot.cpu.effective_cores)
        cpu_pct_cap = int(eff_cores * (Settings.SYSTEM_MAX_CPU_USAGE_PERCENT / 100.0))
        cpu_reserved_cap = eff_cores - Settings.SYSTEM_RESERVED_CPU_CORES
        usable_cpu_threads = max(1, min(cpu_pct_cap, cpu_reserved_cap))

        total_ram_mb = max(1, snapshot.ram.total_bytes // (1024 * 1024))
        avail_ram_mb = max(0, snapshot.ram.available_bytes // (1024 * 1024))
        vidula_rss_mb = max(0, snapshot.ram.vidula_rss_bytes // (1024 * 1024))

        static_ram_cap = min(
            int(total_ram_mb * (Settings.SYSTEM_MAX_RAM_USAGE_PERCENT / 100.0)),
            max(0, total_ram_mb - Settings.SYSTEM_MIN_FREE_RAM_MB),
        )
        external_used_ram_mb = max(0, (total_ram_mb - avail_ram_mb) - vidula_rss_mb)
        dynamic_ram_cap = max(0, total_ram_mb - external_used_ram_mb - Settings.SYSTEM_MIN_FREE_RAM_MB)
        usable_ram_mb = max(0, min(static_ram_cap, dynamic_ram_cap))

        gpu = snapshot.gpu
        gpu_usable = (gpu_health == GpuHealthState.HEALTHY) and (gpu is not None and gpu.is_usable)
        usable_vram_mb = 0
        vram_headroom_mb = 0
        max_gpu_sessions = 0
        if gpu_usable and gpu is not None:
            total_vram_mb = gpu.total_vram_bytes // (1024 * 1024)
            free_vram_mb = gpu.free_vram_bytes // (1024 * 1024)
            vram_static_cap = int(total_vram_mb * (Settings.SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT / 100.0))
            vram_headroom_mb = max(0, free_vram_mb - Settings.SYSTEM_GPU_MIN_FREE_VRAM_MB)
            usable_vram_mb = min(vram_static_cap, vram_headroom_mb)
            per_session_mb = max(1, Settings.SYSTEM_GPU_ENCODE_VRAM_MB)
            max_gpu_sessions = min(Settings.SYSTEM_GPU_MAX_NVENC_SESSIONS, usable_vram_mb // per_session_mb)

        return SystemResourceBudget(
            effective_cores=eff_cores,
            usable_cpu_threads=usable_cpu_threads,
            total_ram_mb=total_ram_mb,
            available_ram_mb=avail_ram_mb,
            external_used_ram_mb=external_used_ram_mb,
            usable_ram_mb=usable_ram_mb,
            gpu_usable=gpu_usable and max_gpu_sessions > 0,
            max_gpu_sessions=max_gpu_sessions,
            usable_vram_mb=usable_vram_mb,
            vram_headroom_mb=vram_headroom_mb,
        )

    def _evaluate_gpu_allocation(
        self,
        profile: WorkloadProfile,
        user_tier: UserTier,
        load_level: LoadLevel,
        snapshot: HardwareTelemetrySnapshot,
        gpu_health: GpuHealthState,
        gpu_health_reason: str,
        budget: SystemResourceBudget,
        ledger: LedgerCommitmentSnapshot,
        unmaterialized_vram_mb: int,
        encoder_available: bool,
    ) -> tuple[bool, int, int, str | None, str | None]:
        if not profile.gpu_capable:
            return False, -1, 0, None, None
        tier_allowed = user_tier.value in self.gpu_allowed_tiers()
        if not tier_allowed:
            return False, -1, 0, None, f"tier_not_gpu_eligible({user_tier.value})"
        if load_level.is_throttled:
            return False, -1, 0, f"load_throttled({load_level.value})", f"load_throttled({load_level.value})"
        if not encoder_available or gpu_health == GpuHealthState.CIRCUIT_OPEN:
            return False, -1, 0, "encoder_circuit_open", "encoder_circuit_open"
        if not budget.gpu_usable or snapshot.gpu is None:
            reason = gpu_health_reason or gpu_health.value
            return False, -1, 0, f"gpu_{gpu_health.value}:{reason}", f"gpu_{gpu_health.value}:{reason}"
        if ledger.committed_gpu_sessions >= budget.max_gpu_sessions:
            reason = f"nvenc_sessions_full({ledger.committed_gpu_sessions}/{budget.max_gpu_sessions})"
            return False, -1, 0, reason, reason

        total_vram_mb = snapshot.gpu.total_vram_bytes // (1024 * 1024)
        vram_static_cap = int(total_vram_mb * (Settings.SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT / 100.0))
        vram_avail = max(
            0,
            min(
                vram_static_cap - ledger.committed_vram_mb,
                budget.vram_headroom_mb - unmaterialized_vram_mb,
            ),
        )
        if vram_avail < profile.vram_reserve_mb:
            reason = f"vram_headroom_low(avail={vram_avail}MB<req={profile.vram_reserve_mb}MB)"
            return False, -1, 0, reason, reason

        return True, snapshot.gpu.device_id, profile.vram_reserve_mb, None, None

    def _compute_thread_allocation(
        self,
        profile: WorkloadProfile,
        user_tier: UserTier,
        load_level: LoadLevel,
        budget: SystemResourceBudget,
        ledger: LedgerCommitmentSnapshot,
        gpu_enabled: bool,
        slot_capacity: int,
    ) -> tuple[Optional[int], str, str, str, Optional[str]]:
        avail_threads = max(0, budget.usable_cpu_threads - ledger.committed_threads)
        if gpu_enabled:
            desired_threads = max(
                profile.min_threads,
                min(Settings.SYSTEM_GPU_ENCODE_CPU_THREADS, profile.max_thread_cap),
            )
            hwaccel = "cuda"
            preferred_encoder = "h264_nvenc"
            token_type = (
                profile.token_type
                if profile.token_type in (TokenType.GPU.value, TokenType.HYBRID.value)
                else TokenType.HYBRID.value
            )
        else:
            ratio = profile.degradation_matrix.get(load_level, 0.0)
            thread_pool = max(1, int(budget.usable_cpu_threads * (ratio if ratio > 0.0 else 0.25)))
            slot_share = max(1, thread_pool // max(1, slot_capacity))
            tier_mult = self.tier_cpu_ratio(user_tier)
            desired_threads = max(
                profile.min_threads,
                int(min(slot_share, profile.max_thread_cap) * tier_mult),
            )
            if user_tier == UserTier.GUEST and load_level.is_throttled:
                desired_threads = 1
            hwaccel = "cpu"
            preferred_encoder = "libx264"
            token_type = (
                TokenType.CPU.value
                if profile.token_type == TokenType.HYBRID.value
                else profile.token_type
            )

        is_compute = profile.token_type in (TokenType.CPU.value, TokenType.HYBRID.value)
        if is_compute and avail_threads < profile.min_threads:
            return None, "", "", "", f"cpu_budget_exhausted({ledger.committed_threads}/{budget.usable_cpu_threads})"
        allocated_threads = max(1, min(desired_threads, max(1, avail_threads)))
        return allocated_threads, hwaccel, preferred_encoder, token_type, None

    def _compute_ram_allocation(
        self,
        profile: WorkloadProfile,
        user_tier: UserTier,
        budget: SystemResourceBudget,
        ledger: LedgerCommitmentSnapshot,
    ) -> tuple[Optional[int], Optional[str]]:
        free_ram_budget = max(0, budget.usable_ram_mb - ledger.committed_ram_mb)
        desired_ram = min(self.tier_ram_mb(user_tier), profile.max_ram_mb)
        if free_ram_budget >= desired_ram:
            return desired_ram, None
        if free_ram_budget >= profile.min_ram_mb:
            return free_ram_budget, None
        if (
            profile.token_type == TokenType.NETWORK.value
            and budget.available_ram_mb >= Settings.SYSTEM_RAM_EMERGENCY_FREE_MB
        ):
            return min(profile.min_ram_mb, desired_ram), None
        return None, f"ram_budget_exhausted({ledger.committed_ram_mb}/{budget.usable_ram_mb}MB)"

    def calculate_permit(
        self,
        profile: WorkloadProfile,
        user_tier: UserTier,
        load_level: LoadLevel,
        snapshot: HardwareTelemetrySnapshot,
        gpu_health: GpuHealthState,
        gpu_health_reason: str,
        budget: SystemResourceBudget,
        ledger: LedgerCommitmentSnapshot,
        unmaterialized_vram_mb: int,
        slot_capacity: int,
        encoder_available: bool = True,
    ) -> tuple[Optional[PermitAllocationDecision], Optional[str]]:
        gpu_enabled, gpu_dev_id, alloc_vram_mb, downgrade_reason, exclusive_deny = self._evaluate_gpu_allocation(
            profile=profile,
            user_tier=user_tier,
            load_level=load_level,
            snapshot=snapshot,
            gpu_health=gpu_health,
            gpu_health_reason=gpu_health_reason,
            budget=budget,
            ledger=ledger,
            unmaterialized_vram_mb=unmaterialized_vram_mb,
            encoder_available=encoder_available,
        )
        if not gpu_enabled:
            if (
                profile.gpu_capable
                and encoder_available
                and gpu_health == GpuHealthState.HEALTHY
                and ledger.committed_gpu_sessions >= budget.max_gpu_sessions
                and user_tier in (UserTier.REGISTERED, UserTier.PREMIUM)
            ):
                return None, exclusive_deny or f"nvenc_sessions_full({ledger.committed_gpu_sessions}/{budget.max_gpu_sessions})"
            if profile.is_exclusive_gpu:
                return None, exclusive_deny or f"gpu_unavailable({gpu_health.value})"

        threads, hwaccel, encoder, token_type, cpu_err = self._compute_thread_allocation(
            profile, user_tier, load_level, budget, ledger, gpu_enabled, slot_capacity,
        )
        if threads is None:
            return None, cpu_err

        allocated_ram_mb, ram_err = self._compute_ram_allocation(
            profile, user_tier, budget, ledger,
        )
        if allocated_ram_mb is None:
            return None, ram_err

        return PermitAllocationDecision(
            allocated_threads=threads,
            allocated_memory_mb=allocated_ram_mb,
            gpu_enabled=gpu_enabled,
            gpu_device_id=gpu_dev_id,
            allocated_vram_mb=alloc_vram_mb,
            hwaccel=hwaccel,
            preferred_encoder=encoder,
            token_type=token_type,
            workload_enum=self.resolve_workload_enum(profile.name, token_type),
            gpu_downgrade_reason=downgrade_reason,
        ), None
