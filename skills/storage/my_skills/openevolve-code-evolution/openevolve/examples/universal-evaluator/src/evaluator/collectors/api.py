import json
import time
from urllib.request import Request, urlopen
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class APICollector(EvidenceCollector):
    name = "api"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        out = []
        for i, request_spec in enumerate(cfg.requests):
            started = time.perf_counter()
            ok = False
            status = 0
            error = ""
            try:
                data = json.dumps(request_spec.json_body).encode() if request_spec.json_body is not None else None
                request = Request(
                    request_spec.url, data=data, headers=request_spec.headers, method=request_spec.method.upper()
                )
                with urlopen(request, timeout=cfg.timeout_seconds or spec.limits.timeout_seconds) as response:
                    status = response.status
                    response.read()
                    ok = status == request_spec.expected_status
            except Exception as exc:
                error = str(exc)
            elapsed = (time.perf_counter() - started) * 1000
            out.append(Evidence(
                id=f"api-request-{i}", collector=self.name, category=EvidenceCategory.CORRECTNESS,
                status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED, value=1.0 if ok else 0.0,
                confidence=1, metadata={"status": status, "latency_ms": elapsed, "error": error},
                duration_ms=elapsed,
                provenance=provenance(candidate, self.version, [request_spec.method, request_spec.url]),
            ))
        return out
