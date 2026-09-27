import time
from .base import EvidenceCollector
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceProvenance, EvidenceStatus


def provenance(candidate, command=None):
    return EvidenceProvenance(candidate_id=candidate.candidate_id, candidate_version=candidate.version, collector_version="0.1.0", command=command or [], environment={})


class TestCollector(EvidenceCollector):
    name = "test"

    async def collect(self, candidate, spec):
        out = []
        sandbox = self.resolve_sandbox(spec)
        for test in spec.tests:
            t = time.perf_counter()
            code, stdout, stderr = await sandbox.run(test.command, cwd=candidate.root, timeout_seconds=spec.limits.timeout_seconds)
            ok = code == 0
            out.append(Evidence(
                id=f"test-{test.name}",
                collector=self.name,
                category=EvidenceCategory.CORRECTNESS,
                status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED,
                value=1.0 if ok else 0.0,
                confidence=1,
                metadata={"returncode": code, "stdout": stdout[-4000:], "stderr": stderr[-4000:]},
                duration_ms=(time.perf_counter() - t) * 1000,
                provenance=provenance(candidate, test.command),
            ))
        return out
