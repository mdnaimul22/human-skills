from __future__ import annotations

from collections.abc import Iterable

from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.metric import MetricValue
from evaluator.models.spec import MetricDefinition
from evaluator.fitness.metrics import MetricDerivationError, derive_metric

from .base import MetricProvider
from .providers import EvidenceFieldProvider


class MetricRegistry:
    def __init__(self, providers: Iterable[MetricProvider] | None = None):
        self._providers: list[MetricProvider] = list(providers or [])

    def register(self, provider: MetricProvider) -> None:
        for existing in self._providers:
            if any(existing.supports(metric_id) for metric_id in getattr(provider, "metric_ids", ())):
                raise ValueError(f"metric provider collision: {provider.name}")
        self._providers.append(provider)

    def provider_for(self, metric_id: str) -> MetricProvider | None:
        for provider in self._providers:
            if provider.supports(metric_id):
                return provider
        return None

    def derive(
        self,
        metric: MetricDefinition,
        evidence: list[Evidence],
        judgments: list[Judgment],
    ) -> MetricValue:
        provider = self.provider_for(metric.id)
        if provider is not None:
            if metric.source is None or metric.source.kind == "evidence" or metric.provider not in {"auto", "canonical"}:
                return provider.derive(metric.id, evidence, judgments)
        try:
            value, ids = derive_metric(metric, evidence, judgments)
        except MetricDerivationError:
            raise
        from evaluator.models.metric import MetricValue
        if metric.source is not None and metric.source.kind == "judgment":
            return MetricValue(metric_id=metric.id, value=value, judgment_ids=ids, provider="declarative", provider_version="1.0.0")
        return MetricValue(metric_id=metric.id, value=value, evidence_ids=ids, provider="declarative", provider_version="1.0.0")

    @classmethod
    def canonical(cls):
        return cls([EvidenceFieldProvider({
            "test_pass_rate": ("test", "value", "mean"),
            "runtime_ms": ("runtime", "value", "mean"),
            "peak_memory_mb": ("resource", "peak_memory_mb", "max"),
            "cpu_time_ms": ("resource", "cpu_time_ms", "mean"),
            "wall_time_ms": ("resource", "wall_time_ms", "mean"),
            "compile_success": ("build", "value", "mean"),
            "query_pass_rate": ("sql", "value", "mean"),
            "query_latency_ms": ("sql", "latency_ms", "mean"),
            "critical_findings": ("security", "critical_findings", "max"),
            "high_findings": ("security", "high_findings", "max"),
            "security_pass": ("security", "value", "mean"),
            "gpu_latency_ms": ("gpu", "latency_ms", "mean"),
            "gpu_memory_mb": ("gpu", "peak_memory_mb", "max"),
            "gpu_throughput": ("gpu", "throughput", "mean"),
            "api_status_pass_rate": ("api", "value", "mean"),
            "api_latency_ms": ("api", "latency_ms", "mean"),
            "line_coverage": ("coverage", "line_coverage", "mean"),
            "branch_coverage": ("coverage", "branch_coverage", "mean"),
            "vulnerable_dependencies": ("dependency", "vulnerable_dependencies", "max"),
            "artifact_valid": ("artifact", "value", "mean"),
        })])
