from __future__ import annotations
import enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from src.helpers import ValidationError


class GpuBackend(str, enum.Enum):
    NONE = "none"
    NVML = "nvml"
    NVIDIA_SMI = "nvidia_smi"
    VAAPI = "vaapi"


class GpuHealthState(str, enum.Enum):
    HEALTHY = "healthy"
    VRAM_PRESSURED = "vram_pressured"
    THERMAL_THROTTLED = "thermal_throttled"
    UTIL_SATURATED = "util_saturated"
    CIRCUIT_OPEN = "circuit_open"
    NVENC_FAILED = "nvenc_failed"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class CpuTelemetry(BaseModel):
    logical_cores: int = Field(ge=1)
    physical_cores: int = Field(ge=1)
    effective_cores: int = Field(default=1, ge=1)
    load_percent: float = Field(default=0.0, ge=0.0)
    raw_load_percent: float = Field(default=0.0, ge=0.0)
    load_1m: float = Field(default=0.0, ge=0.0)
    load_5m: float = Field(default=0.0, ge=0.0)
    load_15m: float = Field(default=0.0, ge=0.0)
    cgroup_quota_cores: Optional[float] = None

    @model_validator(mode="after")
    def validate_cores(self) -> CpuTelemetry:
        if self.logical_cores < self.physical_cores and self.cgroup_quota_cores is None:
            raise ValidationError(f"logical_cores ({self.logical_cores}) cannot be less than physical_cores ({self.physical_cores})")
        if "effective_cores" not in self.model_fields_set:
            if self.cgroup_quota_cores is not None and self.cgroup_quota_cores > 0.0:
                self.effective_cores = max(1, min(self.logical_cores, int(self.cgroup_quota_cores)))
            else:
                self.effective_cores = self.logical_cores
        return self


class RamTelemetry(BaseModel):
    total_bytes: int = Field(ge=1)
    available_bytes: int = Field(ge=0)
    used_bytes: int = Field(ge=0)
    free_bytes: int = Field(ge=0)
    percent: float = Field(default=0.0, ge=0.0)
    swap_total_bytes: int = Field(default=0, ge=0)
    swap_used_bytes: int = Field(default=0, ge=0)
    vidula_rss_bytes: int = Field(default=0, ge=0)


class GpuDeviceTelemetry(BaseModel):
    device_id: int = Field(default=0, ge=0)
    uuid: str = Field(default="")
    name: str = Field(min_length=1)
    total_vram_bytes: int = Field(ge=0)
    free_vram_bytes: int = Field(ge=0)
    used_vram_bytes: int = Field(default=0, ge=0)
    compute_capability: str = Field(pattern=r"^\d+\.\d+$")
    driver_version: str = Field(min_length=1, pattern=r"^[0-9]+(\.[0-9]+)*$")
    gpu_util_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    mem_util_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    temperature_c: int = Field(default=0, ge=0)
    encoder_util_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    active_nvenc_sessions: int = Field(default=0, ge=0)


class GpuTelemetry(BaseModel):
    device_id: int = Field(default=0, ge=0)
    name: str = Field(default="NVIDIA GPU", min_length=1)
    total_vram_bytes: int = Field(default=0, ge=0)
    free_vram_bytes: int = Field(default=0, ge=0)
    compute_capability: str = Field(default="0.0", pattern=r"^\d+\.\d+$")
    driver_version: str = Field(default="0.0", min_length=1, pattern=r"^[0-9]+(\.[0-9]+)*$")
    cuda_available: bool = True
    device_count: int = Field(default=1, ge=0)
    devices: list[GpuDeviceTelemetry] = Field(default_factory=list)
    backend: GpuBackend = GpuBackend.NVML
    nvenc_verified: bool = False
    nvenc_encoders: list[str] = Field(default_factory=list)
    nvenc_failure_reason: Optional[str] = None
    vaapi_available: bool = False
    unavailable_reason: Optional[str] = None

    @model_validator(mode="after")
    def populate_devices(self) -> GpuTelemetry:
        if not self.devices and self.total_vram_bytes > 0:
            self.devices.append(
                GpuDeviceTelemetry(
                    device_id=self.device_id, name=self.name,
                    total_vram_bytes=self.total_vram_bytes, free_vram_bytes=self.free_vram_bytes,
                    used_vram_bytes=max(0, self.total_vram_bytes - self.free_vram_bytes),
                    compute_capability=self.compute_capability, driver_version=self.driver_version,
                )
            )
            self.device_count = len(self.devices)
        return self

    @property
    def is_available(self) -> bool:
        return self.cuda_available and self.total_vram_bytes > 0

    @property
    def is_usable(self) -> bool:
        return self.is_available and self.nvenc_verified


class HardwareTelemetrySnapshot(BaseModel):
    timestamp: float = Field(ge=0.0)
    cpu: CpuTelemetry
    ram: RamTelemetry
    gpu: Optional[GpuTelemetry] = None
    fingerprint: str = Field(default="")
