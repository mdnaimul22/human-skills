import pytest

from evaluator.collectors.registry import CollectorDescriptor, CollectorRegistry
from evaluator.collectors.sql import SQLCollector
from evaluator.engine import EvaluationEngine
from evaluator.models.spec import EvaluationSpec


def sql_spec(**overrides):
    collector = {"id": "sql-main", "type": "sql", "database": ":memory:", **overrides}
    return EvaluationSpec.model_validate({
        "evaluation_id": "e1",
        "objective": "sql",
        "collectors": [collector],
        "fitness": {"metrics": [{"id": "query_pass_rate", "direction": "maximize", "weight": 1}]},
    })


def test_canonical_registry_contains_all_collectors():
    assert CollectorRegistry.canonical().names() == (
        "api", "artifact", "benchmark", "build", "coverage", "dependency",
        "gpu", "resource", "runtime", "security", "sql", "static", "test",
    )


def test_registry_resolves_typed_configuration():
    collectors = CollectorRegistry.canonical().resolve(sql_spec().collectors)
    assert isinstance(collectors[0], SQLCollector)


def test_registry_exposes_capabilities():
    assert "sql" in CollectorRegistry.canonical().capabilities("sql")
    assert "database" in CollectorRegistry.canonical().capabilities("sql")


def test_registry_validates_required_capability():
    spec = sql_spec(required_capabilities=["gpu"])
    with pytest.raises(ValueError, match="required capabilities"):
        CollectorRegistry.canonical().resolve(spec.collectors)


def test_registry_validates_exact_version():
    spec = sql_spec(version="9.9.9")
    with pytest.raises(ValueError, match="version mismatch"):
        CollectorRegistry.canonical().resolve(spec.collectors)


def test_registry_validates_compatible_major_version():
    spec = sql_spec(version="1.x")
    CollectorRegistry.canonical().resolve(spec.collectors)


def test_registry_rejects_unknown_type():
    with pytest.raises(ValueError, match="unknown collector type"):
        CollectorRegistry.canonical().create("does-not-exist")


def test_registry_rejects_duplicate_registration():
    registry = CollectorRegistry.canonical()
    descriptor = registry.descriptor("sql")
    with pytest.raises(ValueError, match="already registered"):
        registry.register(descriptor)


def test_engine_resolves_collectors_from_spec():
    engine = EvaluationEngine()
    collectors = engine.collector_registry.resolve(sql_spec().collectors)
    assert [collector.name for collector in collectors] == ["sql"]


def test_registry_rejects_descriptor_implementation_version_mismatch():
    class BadCollector(SQLCollector):
        name = "sql"
        version = "9.0.0"

    descriptor = CollectorDescriptor(
        "sql", "1.0.0", frozenset({"sql"}),
        type(sql_spec().collectors[0]), BadCollector,
    )
    with pytest.raises(ValueError, match="version mismatch"):
        CollectorRegistry([descriptor])
