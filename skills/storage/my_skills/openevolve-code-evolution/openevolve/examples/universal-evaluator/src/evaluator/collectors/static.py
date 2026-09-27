import time
from .base import EvidenceCollector
from evaluator.models.evidence import *


def provenance(candidate, command=None):
    return EvidenceProvenance(candidate_id=candidate.candidate_id, candidate_version=candidate.version, collector_version="0.1.0", command=command or [], environment={})
class StaticCollector(EvidenceCollector):
    name="static"
    async def collect(self,candidate,spec):
        t=time.perf_counter(); path=candidate.entrypoint_path()
        try: compile(path.read_text(encoding="utf-8"),str(path),"exec"); ok=True
        except (OSError,SyntaxError): ok=False
        return [Evidence(id="static-syntax",collector=self.name,category=EvidenceCategory.STATIC,status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED,value=1.0 if ok else 0.0,confidence=1,metadata={"path":str(path)},duration_ms=(time.perf_counter()-t)*1000,provenance=provenance(candidate))]
