from statistics import median
from typing import Any

from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.spec import MetricDefinition


class MetricDerivationError(ValueError):
    pass


def derive_metric(metric: MetricDefinition, evidence: list[Evidence], judgments: list[Judgment] | None = None) -> tuple[float, list[str]]:
    if metric.source is None:
        raise MetricDerivationError(f"metric {metric.id} has no source and no matching provider")
    if metric.source.kind == "judgment":
        selected_judgments = [j for j in (judgments or []) if j.question_id == metric.source.question_id]
        values: list[float] = []
        judgment_ids: list[str] = []
        for item in selected_judgments:
            raw = getattr(item, metric.source.field, item.value)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                continue
            values.append(float(raw))
            judgment_ids.append(item.question_id)
        if not values:
            raise MetricDerivationError(f"metric {metric.id} has no numeric judgment")
        if metric.source.aggregation == "first":
            result = values[0]
        elif metric.source.aggregation == "last":
            result = values[-1]
        elif metric.source.aggregation == "mean":
            result = sum(values) / len(values)
        elif metric.source.aggregation == "median":
            result = median(values)
        elif metric.source.aggregation == "min":
            result = min(values)
        else:
            result = max(values)
        return result, judgment_ids

    selected = [e for e in evidence if e.collector == metric.source.collector]
    if metric.source.category is not None:
        selected = [e for e in selected if e.category.value == metric.source.category]
    if metric.source.unit is not None:
        selected = [e for e in selected if e.unit == metric.source.unit]

    selected = [e for e in selected if e.status.value == "passed"]
    values: list[float] = []
    evidence_ids: list[str] = []
    for item in selected:
        raw: Any = item.value if metric.source.field == "value" else item.metadata.get(metric.source.field)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            continue
        values.append(float(raw))
        evidence_ids.append(item.id)

    if not values:
        raise MetricDerivationError(f"metric {metric.id} has no numeric evidence")

    if metric.source.aggregation == "first":
        result = values[0]
    elif metric.source.aggregation == "last":
        result = values[-1]
    elif metric.source.aggregation == "mean":
        result = sum(values) / len(values)
    elif metric.source.aggregation == "median":
        result = median(values)
    elif metric.source.aggregation == "min":
        result = min(values)
    else:
        result = max(values)
    return result, evidence_ids
