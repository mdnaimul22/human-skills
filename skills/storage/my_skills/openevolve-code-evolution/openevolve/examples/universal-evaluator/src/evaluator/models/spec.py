from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


Aggregation = Literal["first", "last", "mean", "median", "min", "max"]
CollectorType = Literal[
    "build", "test", "runtime", "benchmark", "static", "sql", "security",
    "gpu", "api", "coverage", "dependency", "resource", "artifact",
]


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    type: Literal["hard_constraint", "optimize"]
    metric: str = Field(min_length=1)


class TestSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    command: list[str] = Field(min_length=1)


class BenchmarkSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    command: list[str] = Field(min_length=1)


class Limits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timeout_seconds: float = Field(default=30, gt=0)
    memory_mb: int = Field(default=1024, gt=0)
    output_kb: int = Field(default=256, gt=0)


class CollectorConfigBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    type: CollectorType
    enabled: bool = True
    timeout_seconds: float | None = Field(default=None, gt=0)
    version: str | None = Field(default=None, min_length=1)
    required_capabilities: list[str] = Field(default_factory=list)


class CommandCollectorConfig(CollectorConfigBase):
    type: Literal["build", "test", "runtime", "benchmark", "static"]


class SQLQuerySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sql: str = Field(min_length=1)
    expected_rows: int | None = Field(default=None, ge=0)


class SQLCollectorConfig(CollectorConfigBase):
    type: Literal["sql"]
    database: str = ":memory:"
    setup: list[str] = Field(default_factory=list)
    queries: list[SQLQuerySpec] = Field(default_factory=list)


class SecurityCollectorConfig(CollectorConfigBase):
    type: Literal["security"]
    tool: str = "bandit"
    command: list[str] | None = None
    severity: Literal["low", "medium", "high", "critical"] = "high"


class GPUCollectorConfig(CollectorConfigBase):
    type: Literal["gpu"]
    command: list[str] = Field(default_factory=lambda: [
        "nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ])


class APIRequestSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=1)
    method: str = Field(default="GET", min_length=1)
    headers: dict[str, str] = Field(default_factory=dict)
    json_body: Any | None = Field(default=None, validation_alias="json", serialization_alias="json")
    expected_status: int = Field(default=200, ge=100, le=599)


class APICollectorConfig(CollectorConfigBase):
    type: Literal["api"]
    requests: list[APIRequestSpec] = Field(default_factory=list)


class CoverageCollectorConfig(CollectorConfigBase):
    type: Literal["coverage"]
    command: list[str] = Field(default_factory=lambda: ["coverage", "run", "-m", "pytest"])
    report_command: list[str] = Field(default_factory=lambda: ["coverage", "report"])


class DependencyCollectorConfig(CollectorConfigBase):
    type: Literal["dependency"]
    scan_command: list[str] | None = None


class ResourceCollectorConfig(CollectorConfigBase):
    type: Literal["resource"]
    command: list[str] | None = None


class ArtifactFileSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1)
    format: Literal["text", "json", "binary"] = "text"


class ArtifactCollectorConfig(CollectorConfigBase):
    type: Literal["artifact"]
    files: list[ArtifactFileSpec] = Field(default_factory=list)


CollectorConfig = Annotated[
    Union[
        CommandCollectorConfig,
        SQLCollectorConfig,
        SecurityCollectorConfig,
        GPUCollectorConfig,
        APICollectorConfig,
        CoverageCollectorConfig,
        DependencyCollectorConfig,
        ResourceCollectorConfig,
        ArtifactCollectorConfig,
    ],
    Field(discriminator="type"),
]


class MetricSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["evidence", "judgment"] = "evidence"
    collector: str | None = None
    category: str | None = None
    question_id: str | None = None
    field: str = Field(default="value", min_length=1)
    unit: str | None = None
    aggregation: Aggregation = "mean"

    @model_validator(mode="after")
    def validate_reference(self):
        if self.kind == "evidence" and not self.collector:
            raise ValueError("evidence metric source requires collector")
        if self.kind == "judgment" and not self.question_id:
            raise ValueError("judgment metric source requires question_id")
        return self


class MetricNormalization(BaseModel):
    model_config = ConfigDict(extra="forbid")
    minimum: float | None = None
    maximum: float | None = None

    @model_validator(mode="after")
    def validate_range(self):
        if self.minimum is not None and self.maximum is not None and self.minimum >= self.maximum:
            raise ValueError("metric normalization minimum must be less than maximum")
        return self


class MetricConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    minimum: float | None = None
    maximum: float | None = None
    hard: bool = False

    @model_validator(mode="after")
    def validate_range(self):
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("metric constraint minimum must not exceed maximum")
        return self


class MetricDefinition(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_shape(cls, value):
        if not isinstance(value, dict):
            return value
        data = dict(value)
        normalization = dict(data.get("normalization") or {})
        constraint = dict(data.get("constraint") or {})
        if "minimum" in data:
            normalization.setdefault("minimum", data.pop("minimum"))
        if "maximum" in data:
            normalization.setdefault("maximum", data.pop("maximum"))
        if "hard" in data:
            constraint.setdefault("hard", data.pop("hard"))
        if "constraint_minimum" in data:
            constraint.setdefault("minimum", data.pop("constraint_minimum"))
        if "constraint_maximum" in data:
            constraint.setdefault("maximum", data.pop("constraint_maximum"))
        if normalization:
            data["normalization"] = normalization
        if constraint:
            data["constraint"] = constraint
        return data

    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    provider: str = "auto"
    direction: Literal["maximize", "minimize"]
    weight: float = Field(gt=0)
    normalization: MetricNormalization = Field(default_factory=MetricNormalization)
    constraint: MetricConstraint = Field(default_factory=MetricConstraint)
    source: MetricSource | None = None

    @property
    def minimum(self) -> float | None:
        return self.normalization.minimum

    @property
    def maximum(self) -> float | None:
        return self.normalization.maximum

    @property
    def hard(self) -> bool:
        return self.constraint.hard

    @property
    def constraint_minimum(self) -> float | None:
        return self.constraint.minimum

    @property
    def constraint_maximum(self) -> float | None:
        return self.constraint.maximum

    @model_validator(mode="after")
    def validate_source(self):
        if self.provider == "auto" and self.source is None:
            return self
        if self.source is None and self.provider not in {"auto", "canonical"}:
            return self
        return self


class FitnessSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metrics: list[MetricDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_metric_ids(self):
        ids = [metric.id for metric in self.metrics]
        if len(ids) != len(set(ids)):
            raise ValueError("fitness metric ids must be unique")
        return self


class JudgeQuestionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    type: Literal["noul", "choice", "score"] = "noul"
    instructions: str = Field(min_length=1)
    criteria: dict[str, str] | list[str] | None = None

    @model_validator(mode="after")
    def validate_criteria(self):
        if self.type == "choice" and not isinstance(self.criteria, dict):
            raise ValueError("choice question requires criteria dict mapping options to descriptions")
        if self.type == "score" and self.criteria is not None and not isinstance(self.criteria, list):
            raise ValueError("score question criteria must be an ordered list of descriptions")
        return self


class EvaluationSpec(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_shape(cls, value):
        if not isinstance(value, dict):
            return value
        data = dict(value)
        if "collectors" not in data and "collector_configs" in data:
            legacy = data.pop("collector_configs") or {}
            collectors = []
            for key, config in legacy.items():
                collector_type = "artifact" if key == "artifacts" else key
                item = dict(config or {})
                item.setdefault("id", key)
                item["type"] = collector_type
                collectors.append(item)
            data["collectors"] = collectors
        return data

    model_config = ConfigDict(extra="forbid")
    evaluation_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    requirements: list[Requirement] = Field(default_factory=list)
    tests: list[TestSpec] = Field(default_factory=list)
    benchmarks: list[BenchmarkSpec] = Field(default_factory=list)
    limits: Limits = Field(default_factory=Limits)
    collectors: list[CollectorConfig] = Field(default_factory=list)
    fitness: FitnessSpec
    judge_questions: list[Union[str, JudgeQuestionSpec]] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    def resolved_judge_questions(self) -> list[JudgeQuestionSpec]:
        result: list[JudgeQuestionSpec] = []
        for q in self.judge_questions:
            if isinstance(q, str):
                result.append(JudgeQuestionSpec(id=q, type="noul", instructions=q))
            else:
                result.append(q)
        return result

    @model_validator(mode="after")
    def validate_references(self):
        metric_ids = {metric.id for metric in self.fitness.metrics}
        unknown = {req.metric for req in self.requirements} - metric_ids
        if unknown:
            raise ValueError(f"requirements reference unknown metrics: {sorted(unknown)}")

        collector_ids = [collector.id for collector in self.collectors]
        if len(collector_ids) != len(set(collector_ids)):
            raise ValueError("collector ids must be unique")

        collector_types = [collector.type for collector in self.collectors]
        if len(collector_types) != len(set(collector_types)):
            raise ValueError("only one configured collector instance per collector type is supported")

        for metric in self.fitness.metrics:
            if metric.source and metric.source.kind == "evidence":
                if metric.source.collector not in collector_types and metric.provider == "auto":
                    continue

        question_ids = {q if isinstance(q, str) else q.id for q in self.judge_questions}
        for metric in self.fitness.metrics:
            if metric.source and metric.source.kind == "judgment":
                if metric.source.question_id and metric.source.question_id not in question_ids and metric.provider == "auto":
                    raise ValueError(f"judgment metric {metric.id} references unknown question_id: '{metric.source.question_id}'")
        return self

    def collector_config(self, collector_type: str) -> CollectorConfig | None:
        for collector in self.collectors:
            if collector.type == collector_type and collector.enabled:
                return collector
        return None
