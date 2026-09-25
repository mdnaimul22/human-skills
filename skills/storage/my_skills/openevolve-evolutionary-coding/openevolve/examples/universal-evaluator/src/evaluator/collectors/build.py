import time
from .base import EvidenceCollector
from evaluator.models.candidate import Candidate
from evaluator.models.evidence import *
from evaluator.models.spec import EvaluationSpec

def provenance(candidate, command=None):
    return EvidenceProvenance(candidate_id=candidate.candidate_id, candidate_version=candidate.version, collector_version="0.1.0", command=command or [], environment={})


class BuildCollector(EvidenceCollector):
    name="build"
    async def collect(self,candidate,spec):
        t=time.perf_counter(); ok=candidate.entrypoint_path().is_file()
        return [Evidence(id="build-entrypoint",collector=self.name,category=EvidenceCategory.BUILD,status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED,value=1.0 if ok else 0.0,confidence=1,metadata={},duration_ms=(time.perf_counter()-t)*1000,provenance=provenance(candidate))]
