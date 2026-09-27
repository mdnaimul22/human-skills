from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict,Field
from .candidate import Candidate
from .evidence import Evidence
from .fitness import FitnessResult
from .judgment import Judgment

class EvaluationRun(BaseModel):
    model_config=ConfigDict(extra="forbid")
    evaluation_id:str; run_id:str; started_at:datetime; finished_at:datetime|None=None; candidate:Candidate; evidence:list[Evidence]=Field(default_factory=list); judgments:list[Judgment]=Field(default_factory=list); fitness:FitnessResult|None=None; artifacts:list[str]=Field(default_factory=list)
    @staticmethod
    def now(): return datetime.now(timezone.utc)
