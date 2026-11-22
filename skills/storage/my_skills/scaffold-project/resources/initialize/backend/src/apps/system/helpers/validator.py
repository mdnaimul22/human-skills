from __future__ import annotations
from typing import Optional
from src.helpers import ValidationError
from ..schema import (
    CpuTelemetry,
    GpuTelemetry,
    HardwareTelemetrySnapshot,
    LoadLevel,
    PermitRequest,
    RamTelemetry,
    ResourceCapacity,
    ResourceLease,
    ThreadBudgetDecision,
    ThrottlingStatus,
    TokenType,
)

VALID_TRANSITIONS: dict[LoadLevel, set[LoadLevel]] = {
    LoadLevel.NORMAL: {LoadLevel.NORMAL, LoadLevel.ELEVATED, LoadLevel.CRITICAL, LoadLevel.EMERGENCY},
    LoadLevel.ELEVATED: {LoadLevel.NORMAL, LoadLevel.ELEVATED, LoadLevel.CRITICAL, LoadLevel.EMERGENCY},
    LoadLevel.CRITICAL: {LoadLevel.NORMAL, LoadLevel.ELEVATED, LoadLevel.CRITICAL, LoadLevel.EMERGENCY},
    LoadLevel.EMERGENCY: {LoadLevel.NORMAL, LoadLevel.ELEVATED, LoadLevel.CRITICAL, LoadLevel.EMERGENCY},
}


class HardwareValidator:
    def validate_cpu(self, cpu: CpuTelemetry) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if cpu.logical_cores < 1:
            errors.append("logical_cores must be >= 1")
        if cpu.physical_cores < 1:
            errors.append("physical_cores must be >= 1")
        if cpu.effective_cores < 1 or cpu.effective_cores > cpu.logical_cores:
            errors.append(f"effective_cores ({cpu.effective_cores}) must be within [1, {cpu.logical_cores}]")
        if cpu.logical_cores < cpu.physical_cores and cpu.cgroup_quota_cores is None:
            errors.append(f"logical_cores ({cpu.logical_cores}) cannot be less than physical_cores ({cpu.physical_cores})")
        if not (0.0 <= cpu.load_percent <= 100.0):
            errors.append(f"load_percent ({cpu.load_percent}) out of bounds [0.0, 100.0]")
        if cpu.load_1m < 0.0 or cpu.load_5m < 0.0 or cpu.load_15m < 0.0:
            errors.append("load averages must be >= 0.0")
        return len(errors) == 0, errors

    def assert_valid_cpu(self, cpu: CpuTelemetry) -> None:
        valid, errors = self.validate_cpu(cpu)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_ram(self, ram: RamTelemetry) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if ram.total_bytes < 1:
            errors.append("total_bytes must be >= 1")
        if ram.available_bytes < 0 or ram.used_bytes < 0 or ram.free_bytes < 0:
            errors.append("RAM byte values must be >= 0")
        if ram.available_bytes > ram.total_bytes:
            errors.append(f"available_bytes ({ram.available_bytes}) exceeds total_bytes ({ram.total_bytes})")
        if ram.used_bytes > ram.total_bytes:
            errors.append(f"used_bytes ({ram.used_bytes}) exceeds total_bytes ({ram.total_bytes})")
        if ram.free_bytes > ram.total_bytes:
            errors.append(f"free_bytes ({ram.free_bytes}) exceeds total_bytes ({ram.total_bytes})")
        if ram.swap_used_bytes > ram.swap_total_bytes:
            errors.append(f"swap_used_bytes ({ram.swap_used_bytes}) exceeds swap_total_bytes ({ram.swap_total_bytes})")
        if not (0.0 <= ram.percent <= 100.0):
            errors.append(f"RAM percent ({ram.percent}) out of bounds [0.0, 100.0]")
        return len(errors) == 0, errors

    def assert_valid_ram(self, ram: RamTelemetry) -> None:
        valid, errors = self.validate_ram(ram)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_gpu(self, gpu: Optional[GpuTelemetry]) -> tuple[bool, list[str]]:
        if gpu is None or not gpu.cuda_available:
            return True, []
        errors: list[str] = []
        if gpu.device_id < 0:
            errors.append("device_id must be >= 0")
        if not gpu.name.strip():
            errors.append("GPU name cannot be empty")
        if gpu.total_vram_bytes < 0 or gpu.free_vram_bytes < 0:
            errors.append("VRAM byte values must be >= 0")
        if gpu.free_vram_bytes > gpu.total_vram_bytes:
            errors.append(f"free_vram_bytes ({gpu.free_vram_bytes}) exceeds total_vram_bytes ({gpu.total_vram_bytes})")
        return len(errors) == 0, errors

    def assert_valid_gpu(self, gpu: Optional[GpuTelemetry]) -> None:
        valid, errors = self.validate_gpu(gpu)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_snapshot(self, snapshot: HardwareTelemetrySnapshot) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if snapshot.timestamp < 0.0:
            errors.append("Snapshot timestamp must be non-negative")
        _, cpu_err = self.validate_cpu(snapshot.cpu)
        errors.extend(cpu_err)
        _, ram_err = self.validate_ram(snapshot.ram)
        errors.extend(ram_err)
        _, gpu_err = self.validate_gpu(snapshot.gpu)
        errors.extend(gpu_err)
        return len(errors) == 0, errors

    def assert_valid_snapshot(self, snapshot: HardwareTelemetrySnapshot) -> None:
        valid, errors = self.validate_snapshot(snapshot)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate(self, snapshot: HardwareTelemetrySnapshot) -> tuple[bool, list[str]]:
        return self.validate_snapshot(snapshot)


class ResourceValidator:
    def validate_lease(self, lease: ResourceLease) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not lease.lease_id.strip():
            errors.append("lease_id cannot be empty")
        if not lease.job_id.strip():
            errors.append("job_id cannot be empty")
        if lease.expires_at < lease.allocated_at:
            errors.append(f"expires_at ({lease.expires_at}) earlier than allocated_at ({lease.allocated_at})")
        if lease.released and lease.is_active:
            errors.append("lease cannot be active while released is True")
        if lease.duration_seconds < 0.0:
            errors.append("duration_seconds must be >= 0.0")
        if lease.cpu_cores_allocated < 1:
            errors.append("cpu_cores_allocated must be >= 1")
        if lease.memory_bytes_allocated < 0:
            errors.append("memory_bytes_allocated must be >= 0")
        if lease.vram_bytes_allocated < 0:
            errors.append("vram_bytes_allocated must be >= 0")
        is_gpu_token = lease.token_type in (TokenType.GPU, TokenType.HYBRID, TokenType.GPU.value, TokenType.HYBRID.value)
        if lease.gpu_device_id >= 0 and not is_gpu_token:
            errors.append("gpu_device_id assigned but token_type is neither GPU nor HYBRID")
        if lease.vram_bytes_allocated > 0 and not is_gpu_token:
            errors.append("vram_bytes_allocated > 0 requires token_type GPU or HYBRID")
        return len(errors) == 0, errors

    def assert_valid_lease(self, lease: ResourceLease) -> None:
        valid, errors = self.validate_lease(lease)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_permit_request(self, req: PermitRequest) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not req.job_id.strip():
            errors.append("job_id cannot be empty")
        if req.timeout < 0.0:
            errors.append("timeout must be >= 0.0")
        if req.ttl_seconds < 1.0:
            errors.append("ttl_seconds must be >= 1.0")
        if req.estimated_cpu_cores < 1:
            errors.append("estimated_cpu_cores must be >= 1")
        if req.estimated_ram_bytes < 0:
            errors.append("estimated_ram_bytes must be >= 0")
        if req.estimated_vram_bytes < 0:
            errors.append("estimated_vram_bytes must be >= 0")
        if not req.requires_gpu and req.estimated_vram_bytes > 0:
            errors.append("requires_gpu is False but estimated_vram_bytes > 0")
        return len(errors) == 0, errors

    def assert_valid_permit_request(self, req: PermitRequest) -> None:
        valid, errors = self.validate_permit_request(req)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_capacity(self, cap: ResourceCapacity) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if cap.total_cpu_cores < 1:
            errors.append("total_cpu_cores must be >= 1")
        if cap.max_encode_slots < 1:
            errors.append("max_encode_slots must be >= 1")
        if cap.max_download_slots < 1:
            errors.append("max_download_slots must be >= 1")
        if cap.active_encode_leases < 0 or cap.active_download_leases < 0:
            errors.append("active lease counts must be >= 0")
        if cap.active_total_leases < (cap.active_encode_leases + cap.active_download_leases):
            errors.append("active_total_leases is less than sum of active category leases")
        return len(errors) == 0, errors

    def assert_valid_capacity(self, cap: ResourceCapacity) -> None:
        valid, errors = self.validate_capacity(cap)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_throttling_status(self, st: ThrottlingStatus) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if st.backoff_factor < 1.0:
            errors.append("backoff_factor must be >= 1.0")
        if not (0.0 <= st.encode_reduction_ratio <= 1.0):
            errors.append(f"encode_reduction_ratio ({st.encode_reduction_ratio}) out of bounds [0.0, 1.0]")
        if not (0.0 <= st.download_reduction_ratio <= 1.0):
            errors.append(f"download_reduction_ratio ({st.download_reduction_ratio}) out of bounds [0.0, 1.0]")
        if st.is_throttled and not st.throttle_reason.strip():
            errors.append("throttle_reason cannot be empty when is_throttled is True")
        return len(errors) == 0, errors

    def assert_valid_throttling_status(self, st: ThrottlingStatus) -> None:
        valid, errors = self.validate_throttling_status(st)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_load_transition(self, current: LoadLevel, target: LoadLevel) -> tuple[bool, list[str]]:
        errors: list[str] = []
        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            errors.append(f"Invalid load level transition from {current.value} to {target.value}")
        return len(errors) == 0, errors

    def assert_valid_load_transition(self, current: LoadLevel, target: LoadLevel) -> None:
        valid, errors = self.validate_load_transition(current, target)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate_thread_budget_decision(self, dec: ThreadBudgetDecision) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if dec.allocated_threads < 1:
            errors.append("allocated_threads must be >= 1")
        if dec.effective_cores > dec.logical_cores:
            errors.append("effective_cores cannot exceed logical_cores")
        return len(errors) == 0, errors

    def assert_valid_thread_budget_decision(self, dec: ThreadBudgetDecision) -> None:
        valid, errors = self.validate_thread_budget_decision(dec)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})

    def validate(
        self,
        target: ResourceLease | PermitRequest | ResourceCapacity | ThrottlingStatus | ThreadBudgetDecision,
    ) -> tuple[bool, list[str]]:
        match target:
            case ResourceLease():
                return self.validate_lease(target)
            case PermitRequest():
                return self.validate_permit_request(target)
            case ResourceCapacity():
                return self.validate_capacity(target)
            case ThrottlingStatus():
                return self.validate_throttling_status(target)
            case ThreadBudgetDecision():
                return self.validate_thread_budget_decision(target)
            case _:
                return False, ["Unsupported validation target type"]

    def assert_valid(
        self,
        target: ResourceLease | PermitRequest | ResourceCapacity | ThrottlingStatus | ThreadBudgetDecision,
    ) -> None:
        valid, errors = self.validate(target)
        if not valid:
            raise ValidationError("; ".join(errors), details={"errors": errors})
