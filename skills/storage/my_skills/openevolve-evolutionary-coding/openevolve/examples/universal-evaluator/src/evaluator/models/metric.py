from pydantic import BaseModel, ConfigDict, Field

class MetricValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_id: str = Field(min_length=1)
    value: float
    evidence_ids: list[str] = Field(default_factory=list)
    judgment_ids: list[str] = Field(default_factory=list)
    provider: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
