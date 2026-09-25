from pydantic import BaseModel, ConfigDict, Field


class MetricResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_id: str
    raw_value: float
    normalized_value: float = Field(ge=0, le=1)
    hard_pass: bool = True
    evidence_ids: list[str] = Field(default_factory=list)
    judgment_ids: list[str] = Field(default_factory=list)


class FitnessResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    valid: bool
    fitness: float
    metrics: list[MetricResult]
    failure_reasons: list[str] = Field(default_factory=list)
