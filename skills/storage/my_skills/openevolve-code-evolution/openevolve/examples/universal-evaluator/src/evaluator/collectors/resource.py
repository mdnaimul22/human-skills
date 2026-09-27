import asyncio
import resource
import time
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class ResourceCollector(EvidenceCollector):
    name = "resource"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        command = cfg.command or [candidate.language, candidate.entrypoint]
        started = time.perf_counter()
        try:
            process = await asyncio.create_subprocess_exec(
                *command, cwd=candidate.root, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=cfg.timeout_seconds or spec.limits.timeout_seconds)
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            wall_ms = (time.perf_counter() - started) * 1000
            return [Evidence(
                id="resource-runtime", collector=self.name, category=EvidenceCategory.PERFORMANCE,
                status=EvidenceStatus.PASSED if process.returncode == 0 else EvidenceStatus.FAILED,
                value=wall_ms, unit="ms", confidence=1,
                metadata={"wall_time_ms": wall_ms, "cpu_time_ms": (usage.ru_utime + usage.ru_stime) * 1000,
                          "peak_memory_mb": usage.ru_maxrss / 1024},
                duration_ms=wall_ms, provenance=provenance(candidate, self.version, command),
            )]
        except asyncio.TimeoutError:
            return [Evidence(
                id="resource-runtime", collector=self.name, category=EvidenceCategory.PERFORMANCE,
                status=EvidenceStatus.FAILED, value=None, confidence=1, metadata={"reason": "timeout"},
                duration_ms=(time.perf_counter() - started) * 1000,
                provenance=provenance(candidate, self.version, command),
            )]
