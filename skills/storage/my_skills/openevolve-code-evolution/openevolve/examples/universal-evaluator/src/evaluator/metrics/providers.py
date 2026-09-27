from statistics import mean
from .base import MetricProvider
from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.metric import MetricValue

class EvidenceFieldProvider(MetricProvider):
    name = "canonical-evidence"
    version = "1.0.0"
    def __init__(self, mapping: dict[str, tuple[str, str, str]]): self.mapping = mapping
    def supports(self, metric_id): return metric_id in self.mapping
    def derive(self, metric_id, evidence, judgments):
        collector, field, aggregation = self.mapping[metric_id]
        selected = [e for e in evidence if e.collector == collector and e.status.value in {"passed", "failed"}]
        vals=[]; ids=[]
        for e in selected:
            raw = e.value if field == "value" else e.metadata.get(field)
            if isinstance(raw, bool):
                raw = 1.0 if raw else 0.0
            if isinstance(raw, (int, float)):
                vals.append(float(raw))
                ids.append(e.id)
        if not vals: raise ValueError(f"metric {metric_id} has no numeric evidence")
        value = vals[0] if aggregation == "first" else vals[-1] if aggregation == "last" else min(vals) if aggregation == "min" else max(vals) if aggregation == "max" else mean(vals)
        return MetricValue(metric_id=metric_id,value=value,evidence_ids=ids,provider=self.name,provider_version=self.version)

class CustomMetricProvider(MetricProvider):
    name = "custom"
    def __init__(self, metric_id, function, version="1.0.0"):
        self.metric_id, self.function, self.version = metric_id, function, version
    def supports(self, metric_id): return metric_id == self.metric_id
    def derive(self, metric_id, evidence, judgments):
        result = self.function(evidence, judgments)
        if not isinstance(result, (int,float)) or isinstance(result,bool): raise TypeError(f"custom metric {metric_id} must return a number")
        return MetricValue(metric_id=metric_id,value=float(result),provider=self.name,provider_version=self.version)
