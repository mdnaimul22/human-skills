from dataclasses import dataclass

from evaluator.models.spec import MetricDefinition


@dataclass(frozen=True)
class ConstraintResult:
    metric_id: str
    passed: bool
    reason: str | None = None


class ConstraintEngine:
    def evaluate(self, metrics: list[MetricDefinition], values: dict[str, float]) -> list[ConstraintResult]:
        results: list[ConstraintResult] = []
        for metric in metrics:
            if not metric.hard:
                continue
            value = values.get(metric.id)
            if value is None:
                results.append(ConstraintResult(metric.id, False, f"missing hard constraint metric: {metric.id}"))
                continue
            if metric.constraint_minimum is not None and value < metric.constraint_minimum:
                results.append(ConstraintResult(metric.id, False, f"constraint failed: {metric.id} < minimum {metric.constraint_minimum}"))
                continue
            if metric.constraint_maximum is not None and value > metric.constraint_maximum:
                results.append(ConstraintResult(metric.id, False, f"constraint failed: {metric.id} > maximum {metric.constraint_maximum}"))
                continue
            results.append(ConstraintResult(metric.id, True))
        return results
