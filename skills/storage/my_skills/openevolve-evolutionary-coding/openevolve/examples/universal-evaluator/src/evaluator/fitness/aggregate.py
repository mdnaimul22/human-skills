from .constraints import ConstraintEngine
from .normalize import normalize
from evaluator.models.fitness import FitnessResult, MetricResult
from evaluator.models.spec import FitnessSpec


def aggregate(spec: FitnessSpec, values: dict[str, float], evidence_ids: dict[str, list[str]] | None = None, judgment_ids: dict[str, list[str]] | None = None) -> FitnessResult:
    evidence_ids = evidence_ids or {}
    judgment_ids = judgment_ids or {}
    constraints = ConstraintEngine().evaluate(spec.metrics, values)
    failures = [result.reason for result in constraints if not result.passed and result.reason]
    results: list[MetricResult] = []

    for metric in spec.metrics:
        if metric.id not in values:
            failures.append(f"missing metric: {metric.id}")
            continue
        try:
            normalized = normalize(values[metric.id], minimum=metric.minimum, maximum=metric.maximum)
        except ValueError as exc:
            failures.append(f"metric {metric.id} normalization failed: {exc}")
            continue
        if metric.direction == "minimize":
            normalized = 1 - normalized
        constraint = next((item for item in constraints if item.metric_id == metric.id), None)
        results.append(
            MetricResult(
                metric_id=metric.id,
                raw_value=values[metric.id],
                normalized_value=normalized,
                hard_pass=constraint.passed if constraint else True,
                evidence_ids=evidence_ids.get(metric.id, []),
                judgment_ids=judgment_ids.get(metric.id, []),
            )
        )

    if failures:
        return FitnessResult(valid=False, fitness=0, metrics=results, failure_reasons=failures)

    total_weight = sum(metric.weight for metric in spec.metrics)
    fitness = sum(
        metric.weight * next(result.normalized_value for result in results if result.metric_id == metric.id)
        for metric in spec.metrics
    ) / total_weight
    return FitnessResult(valid=True, fitness=fitness, metrics=results)
