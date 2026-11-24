from __future__ import annotations
import enum
from pydantic import BaseModel, ConfigDict, Field


class ServiceStatus(str, enum.Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class LivenessStatus(str, enum.Enum):
    OK = "ok"
    ALIVE = "alive"
    SHUTTING_DOWN = "shutting_down"


class SubsystemStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ReadinessStatus(str, enum.Enum):
    READY = "ready"
    DEGRADED = "degraded"
    UNREADY = "unready"


class RootMetadataResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+.*$")
    environment: str = Field(..., min_length=1)
    status: ServiceStatus
    message: str = Field(..., min_length=1)
    server_time: str = Field(..., min_length=1)
    uptime_seconds: float = Field(..., ge=0.0)
    docs_url: str | None = None


class LivenessResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: LivenessStatus
    timestamp: float = Field(..., ge=0.0)
    pid: int = Field(..., gt=0)
    active_jobs: int = Field(..., ge=0)
    version: str = Field(..., min_length=1)


class SubsystemHealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: SubsystemStatus
    latency_ms: float = Field(default=0.0, ge=0.0)
    message: str = ""


class StorageHealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: SubsystemStatus
    free_mb: int = Field(..., ge=0)
    total_mb: int = Field(..., ge=0)
    used_percent: float = Field(..., ge=0.0, le=100.0)
    message: str = ""


class ReadinessChecks(BaseModel):
    model_config = ConfigDict(frozen=True)

    database: SubsystemHealthReport
    storage: StorageHealthReport
    gpu_governor: SubsystemHealthReport
    network_egress: SubsystemHealthReport
    jobs: SubsystemHealthReport


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ReadinessStatus
    timestamp: float = Field(..., ge=0.0)
    version: str = Field(..., min_length=1)
    checks: ReadinessChecks
    degraded_reasons: list[str] = Field(default_factory=list)
