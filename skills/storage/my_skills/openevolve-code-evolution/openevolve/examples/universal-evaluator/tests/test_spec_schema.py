import pytest
from pydantic import ValidationError

from evaluator.models.spec import EvaluationSpec, MetricDefinition


def test_typed_collector_configuration():
    spec = EvaluationSpec.model_validate({
        "evaluation_id": "sql-gpu",
        "objective": "evaluate",
        "collectors": [
            {"id": "sql-main", "type": "sql", "database": ":memory:",
             "setup": ["create table items(id integer)"],
             "queries": [{"sql": "select * from items", "expected_rows": 0}]},
            {"id": "gpu-main", "type": "gpu"},
        ],
        "fitness": {"metrics": [{
            "id": "query_pass_rate", "direction": "maximize", "weight": 1,
        }]},
    })
    sql = spec.collector_config("sql")
    assert sql is not None
    assert sql.type == "sql"
    assert sql.queries[0].expected_rows == 0


def test_collector_config_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        EvaluationSpec.model_validate({
            "evaluation_id": "bad",
            "objective": "evaluate",
            "collectors": [{"id": "sql", "type": "sql", "unknown": True}],
            "fitness": {"metrics": [{"id": "x", "direction": "maximize", "weight": 1}]},
        })


def test_canonical_metric_does_not_require_manual_source():
    metric = MetricDefinition(id="test_pass_rate", direction="maximize", weight=1)
    assert metric.source is None
    assert metric.provider == "auto"


def test_metric_schema_separates_normalization_and_constraint():
    metric = MetricDefinition(
        id="runtime_ms", direction="minimize", weight=1,
        normalization={"minimum": 0, "maximum": 1000},
        constraint={"maximum": 900, "hard": True},
    )
    assert metric.minimum == 0
    assert metric.maximum == 1000
    assert metric.constraint_maximum == 900
    assert metric.hard is True
