import hashlib, os, time
from evaluator.models.evidence import EvidenceProvenance

def provenance(candidate, version, command=None, environment=None):
    return EvidenceProvenance(candidate_id=candidate.candidate_id,candidate_version=candidate.version,collector_version=version,command=command or [],environment=environment or {})

def timed(): return time.perf_counter()
def digest_text(text): return hashlib.sha256(text.encode()).hexdigest()
def env_snapshot(): return {k:os.environ[k] for k in ("PATH","PYTHONPATH") if k in os.environ}
