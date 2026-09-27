import pytest

from evaluator.fitness.aggregate import aggregate
from evaluator.fitness.metrics import derive_metric
from evaluator.fitness.normalize import normalize
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceProvenance, EvidenceStatus
from evaluator.models.spec import FitnessSpec, MetricDefinition, MetricSource


def metric(metric_id, collector, category, **kwargs):
    return MetricDefinition(
        id=metric_id,
        source=MetricSource(collector=collector, category=category, aggregation="mean"),
        direction="maximize",
        weight=1,
        **kwargs,
    )


def evidence(eid, collector, category, value, unit=None):
    return Evidence(
        id=eid,
        collector=collector,
        category=category,
        status=EvidenceStatus.PASSED,
        value=value,
        unit=unit,
        confidence=1,
        duration_ms=1,
        provenance=EvidenceProvenance(candidate_id="candidate-1", collector_version="test"),
    )


def test_normalize():
    assert normalize(50, minimum=0, maximum=100) == 0.5


def test_metric_definition_derives_only_declared_evidence():
    m = metric("correctness", "test", "correctness", minimum=0, maximum=1)
    value, ids = derive_metric(m, [
        evidence("t1", "test", EvidenceCategory.CORRECTNESS, 1),
        evidence("other", "runtime", EvidenceCategory.PERFORMANCE, 999),
    ])
    assert value == 1
    assert ids == ["t1"]


def test_hard_constraint_uses_explicit_threshold():
    m = metric("correctness", "test", "correctness", minimum=0, maximum=1, hard=True, constraint_minimum=1)
    result = aggregate(FitnessSpec(metrics=[m]), {"correctness": 0.8})
    assert not result.valid
    assert result.fitness == 0
    assert "constraint failed: correctness < minimum 1.0" in result.failure_reasons


def test_weighted_fitness():
    a = metric("a", "x", "static", minimum=0, maximum=1)
    b = metric("b", "x", "static", minimum=0, maximum=1)
    assert aggregate(FitnessSpec(metrics=[a, b]), {"a": 1, "b": 0.5}).fitness == 0.75


def test_missing_metric_is_invalid():
    m = metric("x", "x", "static", minimum=0, maximum=1)
    result = aggregate(FitnessSpec(metrics=[m]), {})
    assert not result.valid
    assert result.fitness == 0

from evaluator.evidence_validator import EvidenceValidator
from evaluator.models.candidate import Candidate
from evaluator.models.spec import EvaluationSpec


def test_evidence_validator_rejects_wrong_candidate_provenance(tmp_path):
    candidate = Candidate(candidate_id="candidate-1", root=tmp_path, entrypoint="main.py", language="python")
    spec = EvaluationSpec.model_validate({
        "evaluation_id": "e1", "objective": "test",
        "fitness": {"metrics": [metric("x", "test", "static", minimum=0, maximum=1).model_dump()]},
    })
    item = evidence("x1", "test", EvidenceCategory.STATIC, 1)
    item.provenance = item.provenance.model_copy(update={"candidate_id": "attacker"})
    errors = EvidenceValidator().validate(
        [item], candidate=candidate, spec=spec, run_id="run-1",
        candidate_fingerprint="fp", spec_hash="sh", collector_versions={"test": "0.1.0"},
    )
    assert any("candidate_id provenance mismatch" in e.reason for e in errors)


def test_evidence_validator_rejects_duplicate_ids(tmp_path):
    candidate = Candidate(candidate_id="candidate-1", root=tmp_path, entrypoint="main.py", language="python")
    spec = EvaluationSpec.model_validate({
        "evaluation_id": "e1", "objective": "test",
        "fitness": {"metrics": [metric("x", "test", "static", minimum=0, maximum=1).model_dump()]},
    })
    a = evidence("same", "test", EvidenceCategory.STATIC, 1)
    b = evidence("same", "test", EvidenceCategory.STATIC, 1)
    errors = EvidenceValidator().validate(
        [a, b], candidate=candidate, spec=spec, run_id="run-1",
        candidate_fingerprint="fp", spec_hash="sh", collector_versions={"test": "0.1.0"},
    )
    assert any("duplicate evidence id" in e.reason for e in errors)
