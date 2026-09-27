import asyncio
import time
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class GPUCollector(EvidenceCollector):
    name = "gpu"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        started = time.perf_counter()
        try:
            process = await asyncio.create_subprocess_exec(
                *cfg.command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=cfg.timeout_seconds or spec.limits.timeout_seconds
            )
        except (FileNotFoundError, asyncio.TimeoutError) as exc:
            return [Evidence(
                id="gpu-availability", collector=self.name, category=EvidenceCategory.PERFORMANCE,
                status=EvidenceStatus.SKIPPED, value=None, confidence=1,
                metadata={"reason": str(exc)}, duration_ms=(time.perf_counter() - started) * 1000,
                provenance=provenance(candidate, self.version, cfg.command),
            )]
        rows = []
        for line in stdout.decode(errors="replace").splitlines():
            parts = [item.strip() for item in line.split(",")]
            if len(parts) >= 5:
                rows.append(parts)
        if not rows:
            return [Evidence(
                id="gpu-availability", collector=self.name, category=EvidenceCategory.PERFORMANCE,
                status=EvidenceStatus.FAILED, value=0, confidence=1,
                metadata={"stderr": stderr.decode(errors="replace")},
                duration_ms=(time.perf_counter() - started) * 1000,
                provenance=provenance(candidate, self.version, cfg.command),
            )]
        total = sum(float(row[2]) for row in rows)
        used = sum(float(row[3]) for row in rows)
        utilization = sum(float(row[4]) for row in rows) / len(rows)
        return [Evidence(
            id="gpu-device", collector=self.name, category=EvidenceCategory.PERFORMANCE,
            status=EvidenceStatus.PASSED, value=1.0, confidence=1,
            metadata={"devices": rows, "peak_memory_mb": used, "memory_total_mb": total,
                      "latency_ms": (time.perf_counter() - started) * 1000,
                      "throughput": utilization},
            duration_ms=(time.perf_counter() - started) * 1000,
            provenance=provenance(candidate, self.version, cfg.command),
        )]
