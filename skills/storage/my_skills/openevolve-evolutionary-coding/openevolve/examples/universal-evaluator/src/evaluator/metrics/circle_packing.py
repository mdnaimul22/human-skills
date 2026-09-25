import json
import math
from evaluator.metrics.base import MetricProvider
from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.metric import MetricValue


class CirclePackingMetricProvider(MetricProvider):
    name = "circle_packing"
    version = "1.0.0"
    metric_ids = frozenset({
        "circle_sum_radii",
        "packing_density",
        "valid_packing",
        "overlap_violations",
        "boundary_violations",
    })

    def supports(self, metric_id: str) -> bool:
        return metric_id in self.metric_ids

    def _extract_packing_data(self, evidence: list[Evidence]) -> tuple[list[tuple[float, float]], list[float], list[str]]:
        used_ids: list[str] = []
        for ev in evidence:
            if ev.collector in {"runtime", "artifact", "test"}:
                raw = ev.metadata.get("stdout") or (str(ev.value) if isinstance(ev.value, str) else "")
                if not raw:
                    continue
                try:
                    for line in raw.strip().splitlines():
                        line = line.strip()
                        if line.startswith("{") and line.endswith("}"):
                            data = json.loads(line)
                            if "centers" in data and "radii" in data:
                                centers = [(float(c[0]), float(c[1])) for c in data["centers"]]
                                radii = [float(r) for r in data["radii"]]
                                used_ids.append(ev.id)
                                return centers, radii, used_ids
                except Exception:
                    continue
        return [], [], used_ids

    def derive(self, metric_id: str, evidence: list[Evidence], judgments: list[Judgment]) -> MetricValue:
        centers, radii, used_ids = self._extract_packing_data(evidence)
        if not centers or not radii or len(centers) != len(radii):
            return MetricValue(
                metric_id=metric_id,
                value=0.0,
                evidence_ids=used_ids,
                provider=self.name,
                provider_version=self.version,
            )

        n = len(centers)
        boundary_violations = 0
        overlap_violations = 0
        negative_radii = 0
        eps = 1e-6

        for i in range(n):
            x, y = centers[i]
            r = radii[i]
            if r <= 0 or math.isnan(r) or math.isnan(x) or math.isnan(y):
                negative_radii += 1
            if x - r < -eps or x + r > 1.0 + eps or y - r < -eps or y + r > 1.0 + eps:
                boundary_violations += 1

        for i in range(n):
            for j in range(i + 1, n):
                dx = centers[i][0] - centers[j][0]
                dy = centers[i][1] - centers[j][1]
                dist = math.hypot(dx, dy)
                if dist < (radii[i] + radii[j] - eps):
                    overlap_violations += 1

        is_valid = (boundary_violations == 0 and overlap_violations == 0 and negative_radii == 0)
        sum_radii = sum(radii) if is_valid else 0.0
        density = (math.pi * sum(r * r for r in radii)) if is_valid else 0.0

        if metric_id == "valid_packing":
            val = 1.0 if is_valid else 0.0
        elif metric_id == "circle_sum_radii":
            val = sum_radii
        elif metric_id == "packing_density":
            val = density
        elif metric_id == "overlap_violations":
            val = float(overlap_violations)
        elif metric_id == "boundary_violations":
            val = float(boundary_violations)
        else:
            val = 0.0

        return MetricValue(
            metric_id=metric_id,
            value=float(val),
            evidence_ids=used_ids,
            provider=self.name,
            provider_version=self.version,
        )
