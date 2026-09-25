from abc import ABC, abstractmethod
from evaluator.models.candidate import Candidate
from evaluator.models.evidence import Evidence
from evaluator.models.spec import EvaluationSpec


class EvidenceCollector(ABC):
    name: str
    version: str = "0.1.0"

    def resolve_sandbox(self, spec: EvaluationSpec):
        from evaluator.sandbox.host import HostSandbox
        return getattr(spec, "_sandbox", None) or getattr(self, "sandbox", None) or HostSandbox()

    @abstractmethod
    async def collect(self, candidate: Candidate, spec: EvaluationSpec) -> list[Evidence]:
        raise NotImplementedError
