import asyncio
import re
import shutil
import time
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class CoverageCollector(EvidenceCollector):
    name = "coverage"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        started = time.perf_counter()
        if not shutil.which(cfg.command[0]):
            return [Evidence(
                id="coverage-run", collector=self.name, category=EvidenceCategory.CORRECTNESS,
                status=EvidenceStatus.SKIPPED, value=None, confidence=1,
                metadata={"reason": "coverage command unavailable"}, duration_ms=0,
                provenance=provenance(candidate, self.version, cfg.command),
            )]
        process = await asyncio.create_subprocess_exec(
            *cfg.command, cwd=candidate.root, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=cfg.timeout_seconds or spec.limits.timeout_seconds
        )
        report = await asyncio.create_subprocess_exec(
            *cfg.report_command, cwd=candidate.root, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        report_out, report_err = await report.communicate()
        text = report_out.decode(errors="replace")
        match = re.search(r"TOTAL\s+\S+\s+\S+\s+(\d+)%", text)
        coverage = float(match.group(1)) if match else 0.0
        return [Evidence(
            id="coverage-total", collector=self.name, category=EvidenceCategory.CORRECTNESS,
            status=EvidenceStatus.PASSED if process.returncode == 0 else EvidenceStatus.FAILED,
            value=coverage, unit="percent", confidence=1,
            metadata={"line_coverage": coverage, "branch_coverage": 0.0,
                      "stdout": text[-4000:], "stderr": (stderr + report_err).decode(errors="replace")[-2000:]},
            duration_ms=(time.perf_counter() - started) * 1000,
            provenance=provenance(candidate, self.version, cfg.command),
        )]
