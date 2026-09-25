import asyncio
import json
import shutil
import time
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class SecurityCollector(EvidenceCollector):
    name = "security"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        command = cfg.command or [cfg.tool, "-r", str(candidate.root), "-f", "json"]
        started = time.perf_counter()
        if not shutil.which(command[0]):
            return [Evidence(
                id="security-scanner", collector=self.name, category=EvidenceCategory.SECURITY,
                status=EvidenceStatus.SKIPPED, value=None, confidence=1,
                metadata={"reason": f"scanner not installed: {command[0]}"}, duration_ms=0,
                provenance=provenance(candidate, self.version, command),
            )]
        try:
            process = await asyncio.create_subprocess_exec(
                *command, cwd=candidate.root, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=cfg.timeout_seconds or spec.limits.timeout_seconds
            )
        except asyncio.TimeoutError:
            return [Evidence(
                id="security-scan", collector=self.name, category=EvidenceCategory.SECURITY,
                status=EvidenceStatus.FAILED, value=0.0, confidence=1,
                metadata={"reason": "timeout"}, duration_ms=(time.perf_counter() - started) * 1000,
                provenance=provenance(candidate, self.version, command),
            )]

        critical = high = medium = 0
        try:
            data = json.loads(stdout.decode(errors="replace"))
            for finding in data.get("results", []):
                severity = str(finding.get("issue_severity", "")).lower()
                critical += severity == "critical"
                high += severity == "high"
                medium += severity == "medium"
        except (json.JSONDecodeError, TypeError):
            pass
        ok = critical == 0 and high == 0
        return [Evidence(
            id="security-scan", collector=self.name, category=EvidenceCategory.SECURITY,
            status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED,
            value=1.0 if ok else 0.0, confidence=1,
            metadata={"critical_findings": critical, "high_findings": high, "medium_findings": medium,
                      "stdout": stdout.decode(errors="replace")[-8000:],
                      "stderr": stderr.decode(errors="replace")[-2000:]},
            duration_ms=(time.perf_counter() - started) * 1000,
            provenance=provenance(candidate, self.version, command),
        )]
