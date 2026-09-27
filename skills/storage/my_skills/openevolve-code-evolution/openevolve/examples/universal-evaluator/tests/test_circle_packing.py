import json
import pytest
from evaluator.metrics.circle_packing import CirclePackingMetricProvider
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceProvenance, EvidenceStatus


def make_evidence(data: dict) -> list[Evidence]:
    return [
        Evidence(
            id="e_runtime_test",
            collector="runtime",
            category=EvidenceCategory.PERFORMANCE,
            status=EvidenceStatus.PASSED,
            value=10.0,
            confidence=1.0,
            duration_ms=10.0,
            unit="ms",
            provenance=EvidenceProvenance(candidate_id="c_test", collector_version="1.0.0"),
            metadata={"stdout": json.dumps(data)},
        )
    ]


def test_circle_packing_metric_valid_configuration():
    provider = CirclePackingMetricProvider()
    data = {
        "centers": [[0.2, 0.2], [0.8, 0.8]],
        "radii": [0.1, 0.1],
    }
    evidence = make_evidence(data)
    valid_res = provider.derive("valid_packing", evidence, [])
    assert valid_res.value == 1.0

    sum_res = provider.derive("circle_sum_radii", evidence, [])
    assert pytest.approx(sum_res.value, rel=1e-4) == 0.2

    density_res = provider.derive("packing_density", evidence, [])
    assert density_res.value > 0.0


def test_circle_packing_metric_detects_overlaps():
    provider = CirclePackingMetricProvider()
    data = {
        "centers": [[0.5, 0.5], [0.5, 0.5]],
        "radii": [0.3, 0.3],
    }
    evidence = make_evidence(data)
    valid_res = provider.derive("valid_packing", evidence, [])
    assert valid_res.value == 0.0

    overlap_res = provider.derive("overlap_violations", evidence, [])
    assert overlap_res.value == 1.0

    sum_res = provider.derive("circle_sum_radii", evidence, [])
    assert sum_res.value == 0.0


def test_circle_packing_metric_detects_boundary_escape():
    provider = CirclePackingMetricProvider()
    data = {
        "centers": [[1.5, 1.5]],
        "radii": [0.2],
    }
    evidence = make_evidence(data)
    valid_res = provider.derive("valid_packing", evidence, [])
    assert valid_res.value == 0.0

    boundary_res = provider.derive("boundary_violations", evidence, [])
    assert boundary_res.value == 1.0
