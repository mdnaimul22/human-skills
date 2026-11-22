from __future__ import annotations
import enum
import time
import uuid
from pydantic import BaseModel, Field, model_validator
from src.helpers import ValidationError

class UserTier(str, enum.Enum):
    GUEST = "guest"
    REGISTERED = "registered"
    PREMIUM = "premium"

class LoadLevel(str, enum.Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

    @property
    def is_throttled(self) -> bool:
        return self in (LoadLevel.CRITICAL, LoadLevel.EMERGENCY)

    @property
    def severity_rank(self) -> int:
        ranks = {LoadLevel.NORMAL: 0, LoadLevel.ELEVATED: 1, LoadLevel.CRITICAL: 2, LoadLevel.EMERGENCY: 3}
        return ranks[self]

class WorkloadType(str, enum.Enum):
    DOWNLOAD = "download"
    ENCODE = "encode"
    DIRECT = "direct"
    PROBE = "probe"
    AUDIO = "audio"
    ML = "ml"
    RENDER = "render"
    EGRESS = "egress"

class TokenType(str, enum.Enum):
    CPU = "cpu"
    GPU = "gpu"
    HYBRID = "hybrid"
    NETWORK = "network"
    RAM = "ram"

class WorkloadProfile(BaseModel):
    name: str = Field(min_length=1)
    token_type: str = Field(default=TokenType.CPU.value)
    base_slots: int = Field(default=2, ge=1)
    default_ttl: float = Field(default=300.0, ge=1.0)
    degradation_matrix: dict[LoadLevel, float] = Field(
        default_factory=lambda: {
            LoadLevel.NORMAL: 1.0,
            LoadLevel.ELEVATED: 0.75,
            LoadLevel.CRITICAL: 0.25,
            LoadLevel.EMERGENCY: 0.0,
        }
    )
    max_thread_cap: int = Field(default=16, ge=1)
    min_threads: int = Field(default=1, ge=1)
    min_ram_mb: int = Field(default=64, ge=1)
    max_ram_mb: int = Field(default=2048, ge=1)
    gpu_capable: bool = Field(default=False)
    vram_reserve_mb: int = Field(default=0, ge=0)
    is_exclusive_gpu: bool = Field(default=False)

    @model_validator(mode="after")
    def normalize_profile(self) -> WorkloadProfile:
        self.name = self.name.strip().lower()
        return self

    def calculate_capacity(self, load_level: LoadLevel) -> int:
        ratio = self.degradation_matrix.get(load_level, 0.0)
        if ratio <= 0.0:
            return 0
        return max(1, int(self.base_slots * ratio))

    def calculate_threads(self, logical_cores: int, load_level: LoadLevel) -> int:
        cores = max(1, logical_cores)
        ratio = self.degradation_matrix.get(load_level, 0.0)
        if ratio <= 0.0:
            return 1
        allocated = int(cores * ratio)
        return max(1, min(allocated if allocated > 0 else 1, self.max_thread_cap))

class ResourceLease(BaseModel):
    lease_id: str = Field(default_factory=lambda: f"lease_{uuid.uuid4().hex[:12]}")
    job_id: str = Field(min_length=1)
    workload_type: str = Field(min_length=1)
    token_type: str = Field(default=TokenType.CPU.value)
    allocated_at: float = Field(default_factory=time.time, ge=0.0)
    expires_at: float = Field(default=0.0, ge=0.0)
    duration_seconds: float = Field(default=300.0, ge=0.0)
    released: bool = Field(default=False)
    is_active: bool = Field(default=True)
    cpu_cores_allocated: int = Field(default=1, ge=1)
    gpu_device_id: int = Field(default=-1)
    memory_bytes_allocated: int = Field(default=0, ge=0)
    vram_bytes_allocated: int = Field(default=0, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_lease_state(self) -> ResourceLease:
        if self.expires_at <= 0.0:
            self.expires_at = self.allocated_at + self.duration_seconds
        if self.expires_at < self.allocated_at:
            raise ValidationError(f"expires_at ({self.expires_at}) cannot be before allocated_at ({self.allocated_at})")
        if self.released:
            self.is_active = False
        return self

    def release(self) -> None:
        self.released = True
        self.is_active = False

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class ResourcePermit(BaseModel):
    permit_id: str = Field(default_factory=lambda: f"permit_{uuid.uuid4().hex[:12]}")
    job_id: str = Field(default="")
    user_tier: UserTier = Field(default=UserTier.GUEST)
    workload_type: WorkloadType = Field(default=WorkloadType.DOWNLOAD)
    workload_name: str = Field(default="")
    allocated_threads: int = Field(default=1, ge=1)
    allocated_memory_mb: int = Field(default=256, ge=1)
    network_slot_id: str | None = Field(default=None)
    gpu_enabled: bool = Field(default=False)
    gpu_device_id: int = Field(default=-1)
    hwaccel: str = Field(default="cpu")
    preferred_encoder: str = Field(default="libx264")
    allocated_vram_mb: int = Field(default=0, ge=0)
    gpu_downgrade_reason: str | None = Field(default=None)
    acquired_at: float = Field(default_factory=time.time, ge=0.0)
    released: bool = Field(default=False)
    lease: ResourceLease | None = None

    def release(self) -> None:
        self.released = True

class PermitRequest(BaseModel):
    job_id: str = Field(min_length=1)
    workload_type: str = Field(min_length=1)
    timeout: float = Field(default=5.0, ge=0.0)
    priority: int = Field(default=0, ge=0)
    estimated_cpu_cores: int = Field(default=1, ge=1)
    estimated_ram_bytes: int = Field(default=0, ge=0)
    requires_gpu: bool = Field(default=False)
    estimated_vram_bytes: int = Field(default=0, ge=0)
    ttl_seconds: float = Field(default=300.0, ge=1.0)
    client_ip: str = Field(default="")
    user_id: str = Field(default="")
    user_tier: UserTier = Field(default=UserTier.GUEST)

class ResourceCapacity(BaseModel):
    total_cpu_cores: int = Field(ge=1)
    max_encode_slots: int = Field(ge=1)
    max_download_slots: int = Field(ge=1)
    max_queue_depth: int = Field(default=100, ge=1)
    active_encode_leases: int = Field(default=0, ge=0)
    active_download_leases: int = Field(default=0, ge=0)
    active_total_leases: int = Field(default=0, ge=0)
    load_level: LoadLevel = Field(default=LoadLevel.NORMAL)
    cpu_load_percent: float = Field(default=0.0, ge=0.0)
    available_ram_bytes: int = Field(default=0, ge=0)
    free_vram_bytes: int = Field(default=0, ge=0)
    workload_capacities: dict[str, int] = Field(default_factory=dict)
    active_leases_by_workload: dict[str, int] = Field(default_factory=dict)

    @property
    def available_encode_slots(self) -> int:
        return max(0, self.max_encode_slots - self.active_encode_leases)

    @property
    def available_download_slots(self) -> int:
        return max(0, self.max_download_slots - self.active_download_leases)

class ThrottlingStatus(BaseModel):
    is_throttled: bool = Field(default=False)
    load_level: LoadLevel = Field(default=LoadLevel.NORMAL)
    throttle_reason: str = Field(default="")
    backoff_factor: float = Field(default=1.0, ge=1.0)
    encode_reduction_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    download_reduction_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    throttled_at: float = Field(default=0.0, ge=0.0)
    recovery_recommendation: str = Field(default="")

class LeaseReapReport(BaseModel):
    reaped_count: int = Field(default=0, ge=0)
    reaped_lease_ids: list[str] = Field(default_factory=list)
    scanned_count: int = Field(default=0, ge=0)
    reaped_at: float = Field(default_factory=time.time, ge=0.0)

class ThreadBudgetDecision(BaseModel):
    workload: str = Field(min_length=1)
    load_level: LoadLevel = Field(default=LoadLevel.NORMAL)
    logical_cores: int = Field(ge=1)
    effective_cores: int = Field(ge=1)
    active_jobs: int = Field(default=1, ge=1)
    hw_accel: bool = Field(default=False)
    allocated_threads: int = Field(ge=1)


class SystemResourceBudget(BaseModel):
    effective_cores: int = Field(ge=1)
    usable_cpu_threads: int = Field(ge=1)
    total_ram_mb: int = Field(ge=1)
    available_ram_mb: int = Field(ge=0)
    external_used_ram_mb: int = Field(ge=0)
    usable_ram_mb: int = Field(ge=0)
    gpu_usable: bool = False
    max_gpu_sessions: int = Field(default=0, ge=0)
    usable_vram_mb: int = Field(default=0, ge=0)
    vram_headroom_mb: int = Field(default=0, ge=0)


class LedgerCommitmentSnapshot(BaseModel):
    active_leases: int = Field(default=0, ge=0)
    committed_threads: int = Field(default=0, ge=0)
    committed_ram_mb: int = Field(default=0, ge=0)
    committed_gpu_sessions: int = Field(default=0, ge=0)
    committed_vram_mb: int = Field(default=0, ge=0)
    active_by_workload: dict[str, int] = Field(default_factory=dict)
