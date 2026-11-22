from __future__ import annotations
import enum
from typing import Optional
from pydantic import BaseModel, Field

class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class EncoderCircuitState(BaseModel):
    encoder_name: str
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = Field(default=0, ge=0)
    total_failures: int = Field(default=0, ge=0)
    total_successes: int = Field(default=0, ge=0)
    last_failure_time: float = Field(default=0.0, ge=0.0)
    last_success_time: float = Field(default=0.0, ge=0.0)
    cooldown_until: float = Field(default=0.0, ge=0.0)
    last_error_reason: Optional[str] = None
    half_open_in_flight: bool = False
    half_open_lease_expiry: float = Field(default=0.0, ge=0.0)
