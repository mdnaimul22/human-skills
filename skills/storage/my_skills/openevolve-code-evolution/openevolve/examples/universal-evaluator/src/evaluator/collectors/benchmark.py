import time
from .base import EvidenceCollector
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceProvenance, EvidenceStatus


def provenance(candidate, command=None):
    return EvidenceProvenance(candidate_id=candidate.candidate_id, candidate_version=candidate.version, collector_version="0.1.0", command=command or [], environment={})


class BenchmarkCollector(EvidenceCollector):
    name = "benchmark"

    async def collect(self, candidate, spec):
        out = []
        sandbox = self.resolve_sandbox(spec)
        for b in spec.benchmarks:
            t = time.perf_counter()
            code, stdout, stderr = await sandbox.run(b.command, cwd=candidate.root, timeout_seconds=spec.limits.timeout_seconds)
            ok = code == 0
            out.append(Evidence(
                id=f"benchmark-{b.name}",
                collector=self.name,
                category=EvidenceCategory.PERFORMANCE,
                status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED,
                value=1.0 if ok else 0.0,
                confidence=1,
                metadata={"returncode": code, "stdout": stdout[-4000:], "stderr": stderr[-4000:]},
                duration_ms=(time.perf_counter() - t) * 1000,
                provenance=provenance(candidate, b.command),
            ))
        return out
