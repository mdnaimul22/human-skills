import json
import time
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class ArtifactCollector(EvidenceCollector):
    name = "artifact"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        out = []
        for i, artifact in enumerate(cfg.files):
            started = time.perf_counter()
            path = (candidate.root / artifact.path).resolve()
            ok = path.is_file()
            error = ""
            if ok and artifact.format == "json":
                try:
                    json.loads(path.read_text())
                except Exception as exc:
                    ok = False
                    error = str(exc)
            out.append(Evidence(
                id=f"artifact-{i}", collector=self.name, category=EvidenceCategory.STATIC,
                status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED, value=1.0 if ok else 0.0,
                confidence=1, metadata={"path": str(path), "error": error,
                                         "size_bytes": path.stat().st_size if path.exists() else 0},
                duration_ms=(time.perf_counter() - started) * 1000,
                provenance=provenance(candidate, self.version, ["artifact", str(path)]),
            ))
        return out
