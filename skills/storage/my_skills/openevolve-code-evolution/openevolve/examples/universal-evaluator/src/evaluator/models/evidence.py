from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class EvidenceCategory(StrEnum):
    BUILD = "build"
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"
    MEMORY = "memory"
    STATIC = "static"
    SECURITY = "security"
    SEMANTIC = "semantic"


class EvidenceStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class EvidenceProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str = Field(min_length=1)
    candidate_version: str | None = None
    candidate_fingerprint: str | None = None
    evaluation_id: str | None = None
    run_id: str | None = None
    spec_hash: str | None = None
    collector_version: str | None = None
    command: list[str] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)
    artifact_refs: list[str] = Field(default_factory=list)
    stdout_hash: str | None = None
    stderr_hash: str | None = None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    collector: str = Field(min_length=1)
    category: EvidenceCategory
    status: EvidenceStatus
    value: float | int | str | bool | None = None
    unit: str | None = None
    confidence: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = Field(ge=0)
    reproducible: bool = True
    provenance: EvidenceProvenance
