import time
from .base import EvidenceCollector
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceProvenance, EvidenceStatus


def provenance(candidate, command=None):
    return EvidenceProvenance(candidate_id=candidate.candidate_id, candidate_version=candidate.version, collector_version="0.1.0", command=command or [], environment={})


class RuntimeCollector(EvidenceCollector):
    name = "runtime"

    async def collect(self, candidate, spec):
        t = time.perf_counter()
        sandbox = self.resolve_sandbox(spec)
        cmd = ["python", str(candidate.entrypoint_path())]
        code, stdout, stderr = await sandbox.run(cmd, cwd=candidate.root, timeout_seconds=spec.limits.timeout_seconds)
        ok = code == 0
        ms = (time.perf_counter() - t) * 1000
        return [Evidence(
            id="runtime-execution",
            collector=self.name,
            category=EvidenceCategory.PERFORMANCE,
            status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED,
            value=ms,
            unit="ms",
            confidence=1,
            metadata={"returncode": code, "stdout": stdout[-4000:], "stderr": stderr[-4000:]},
            duration_ms=ms,
            provenance=provenance(candidate, cmd),
        )]
