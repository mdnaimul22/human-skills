from abc import ABC, abstractmethod
from evaluator.models.candidate import Candidate
from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.spec import EvaluationSpec

class TypedJudge(ABC):
    name: str

    @abstractmethod
    async def judge(
        self,
        spec: EvaluationSpec,
        evidence: list[Evidence],
        candidate: Candidate | None = None,
    ) -> list[Judgment]:
        raise NotImplementedError
