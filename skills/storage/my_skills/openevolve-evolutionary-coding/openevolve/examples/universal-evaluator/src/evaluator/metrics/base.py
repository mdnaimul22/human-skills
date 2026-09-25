from abc import ABC, abstractmethod
from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.metric import MetricValue

class MetricProvider(ABC):
    name: str
    version: str = "1.0.0"
    @abstractmethod
    def supports(self, metric_id: str) -> bool: ...
    @abstractmethod
    def derive(self, metric_id: str, evidence: list[Evidence], judgments: list[Judgment]) -> MetricValue: ...
