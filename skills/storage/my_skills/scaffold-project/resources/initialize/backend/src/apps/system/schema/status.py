from __future__ import annotations
from pydantic import BaseModel, Field
from .breaker import EncoderCircuitState
from .hardware import GpuHealthState, HardwareTelemetrySnapshot
from .resource import LedgerCommitmentSnapshot, LoadLevel, SystemResourceBudget


class SystemStatusSnapshot(BaseModel):
    timestamp: float = Field(ge=0.0)
    hardware: HardwareTelemetrySnapshot
    load_level: LoadLevel
    gpu_health: GpuHealthState
    budget: SystemResourceBudget
    ledger: LedgerCommitmentSnapshot
    workload_capacities: dict[str, int] = Field(default_factory=dict)
    encoder_circuits: dict[str, EncoderCircuitState] = Field(default_factory=dict)
    active_limits: dict[str, float | int | bool | str] = Field(default_factory=dict)
