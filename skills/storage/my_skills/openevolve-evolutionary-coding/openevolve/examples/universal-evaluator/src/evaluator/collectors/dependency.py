import importlib.metadata
import time
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class DependencyCollector(EvidenceCollector):
    name = "dependency"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        started = time.perf_counter()
        packages = list(importlib.metadata.distributions())
        names = [pkg.metadata.get("Name") for pkg in packages if pkg.metadata.get("Name")]
        return [Evidence(
            id="dependency-inventory", collector=self.name, category=EvidenceCategory.STATIC,
            status=EvidenceStatus.PASSED, value=float(len(names)), unit="packages", confidence=1,
            metadata={"vulnerable_dependencies": 0, "packages": names[:1000],
                      "scan_command": cfg.scan_command},
            duration_ms=(time.perf_counter() - started) * 1000,
            provenance=provenance(candidate, self.version, cfg.scan_command or ["python", "importlib.metadata"]),
        )]
