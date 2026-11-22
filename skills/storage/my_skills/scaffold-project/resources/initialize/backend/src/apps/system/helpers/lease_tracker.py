from __future__ import annotations
import threading
import time
import uuid
from typing import Optional
from src.config import Settings, setup_logger
from ..schema import LedgerCommitmentSnapshot, ResourceLease, TokenType

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.lease_tracker")


class LeaseTracker:
    def __init__(self, default_ttl: Optional[float] = None) -> None:
        self._explicit_ttl = default_ttl
        self._leases: dict[str, ResourceLease] = {}
        self._job_to_lease: dict[str, str] = {}
        self._committed_threads: int = 0
        self._committed_ram_bytes: int = 0
        self._committed_gpu_sessions: int = 0
        self._committed_vram_bytes: int = 0
        self._active_by_workload: dict[str, int] = {}
        self._lock = threading.Lock()

    @property
    def default_ttl(self) -> float:
        if self._explicit_ttl is not None:
            return self._explicit_ttl
        return Settings.SYSTEM_DEFAULT_LEASE_TTL_SEC

    def _increment_ledger_locked(self, lease: ResourceLease) -> None:
        self._committed_threads += max(1, lease.cpu_cores_allocated)
        self._committed_ram_bytes += max(0, lease.memory_bytes_allocated)
        if lease.gpu_device_id >= 0:
            self._committed_gpu_sessions += 1
        self._committed_vram_bytes += max(0, lease.vram_bytes_allocated)
        w = lease.workload_type
        self._active_by_workload[w] = self._active_by_workload.get(w, 0) + 1

    def _decrement_ledger_locked(self, lease: ResourceLease) -> None:
        self._committed_threads = max(0, self._committed_threads - max(1, lease.cpu_cores_allocated))
        self._committed_ram_bytes = max(0, self._committed_ram_bytes - max(0, lease.memory_bytes_allocated))
        if lease.gpu_device_id >= 0:
            self._committed_gpu_sessions = max(0, self._committed_gpu_sessions - 1)
        self._committed_vram_bytes = max(0, self._committed_vram_bytes - max(0, lease.vram_bytes_allocated))
        w = lease.workload_type
        if w in self._active_by_workload:
            next_val = self._active_by_workload[w] - 1
            if next_val > 0:
                self._active_by_workload[w] = next_val
            else:
                self._active_by_workload.pop(w, None)

    def create_lease(
        self,
        workload_type: str,
        job_id: str,
        ttl: Optional[float] = None,
        token_type: str = TokenType.CPU.value,
        cpu_cores_allocated: int = 1,
        memory_bytes_allocated: int = 0,
        gpu_device_id: int = -1,
        vram_bytes_allocated: int = 0,
    ) -> ResourceLease:
        norm_type = workload_type.lower()
        token_val = token_type.lower()
        now = time.time()
        effective_ttl = ttl if (ttl is not None and ttl > 0.0) else self.default_ttl
        lease_id = f"lse_{uuid.uuid4().hex[:12]}"
        lease = ResourceLease(
            lease_id=lease_id,
            job_id=job_id,
            workload_type=norm_type,
            token_type=token_val,
            allocated_at=now,
            expires_at=now + effective_ttl,
            duration_seconds=effective_ttl,
            released=False,
            is_active=True,
            cpu_cores_allocated=max(1, cpu_cores_allocated),
            gpu_device_id=gpu_device_id,
            memory_bytes_allocated=max(0, memory_bytes_allocated),
            vram_bytes_allocated=max(0, vram_bytes_allocated),
        )
        with self._lock:
            self._leases[lease_id] = lease
            self._job_to_lease[job_id] = lease_id
            self._increment_ledger_locked(lease)
        return lease

    def release_lease(self, lease: ResourceLease) -> bool:
        with self._lock:
            if lease.released:
                return False
            tracked = self._leases.pop(lease.lease_id, None)
            lease.release()
            if self._job_to_lease.get(lease.job_id) == lease.lease_id:
                self._job_to_lease.pop(lease.job_id, None)
            if tracked is not None:
                self._decrement_ledger_locked(tracked)
            return True

    def reap_expired(self, now: Optional[float] = None) -> list[ResourceLease]:
        current_time = now if now is not None else time.time()
        expired: list[ResourceLease] = []
        with self._lock:
            for lease_id, lease in list(self._leases.items()):
                if not lease.released and lease.expires_at <= current_time:
                    lease.release()
                    expired.append(lease)
                    self._leases.pop(lease_id, None)
                    if self._job_to_lease.get(lease.job_id) == lease_id:
                        self._job_to_lease.pop(lease.job_id, None)
                    self._decrement_ledger_locked(lease)
        return expired

    def get_lease(self, lease_id: str) -> Optional[ResourceLease]:
        with self._lock:
            return self._leases.get(lease_id)

    def get_lease_by_job(self, job_id: str) -> Optional[ResourceLease]:
        with self._lock:
            lease_id = self._job_to_lease.get(job_id)
            return self._leases.get(lease_id) if lease_id else None

    def active_count(self) -> int:
        with self._lock:
            return len(self._leases)

    def get_commitment_snapshot(self) -> LedgerCommitmentSnapshot:
        with self._lock:
            return LedgerCommitmentSnapshot(
                active_leases=len(self._leases),
                committed_threads=self._committed_threads,
                committed_ram_mb=self._committed_ram_bytes // (1024 * 1024),
                committed_gpu_sessions=self._committed_gpu_sessions,
                committed_vram_mb=self._committed_vram_bytes // (1024 * 1024),
                active_by_workload=dict(self._active_by_workload),
            )

    def get_unmaterialized_vram_mb(self, window_sec: float) -> int:
        now = time.time()
        total_bytes = 0
        with self._lock:
            for lease in self._leases.values():
                if not lease.released and lease.vram_bytes_allocated > 0 and (now - lease.allocated_at) <= window_sec:
                    total_bytes += lease.vram_bytes_allocated
        return total_bytes // (1024 * 1024)

