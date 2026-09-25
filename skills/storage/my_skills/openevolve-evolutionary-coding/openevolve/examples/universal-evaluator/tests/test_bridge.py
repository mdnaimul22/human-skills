from pathlib import Path
import pytest

from evaluator.bridge import OpenEvolveBridge, make_evaluator
from evaluator.judges.base import TypedJudge
from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.spec import EvaluationSpec


class MockJudge(TypedJudge):
    name = "mock_jev"

    async def judge(self, spec: EvaluationSpec, evidence: list[Evidence]) -> list[Judgment]:
        return [
            Judgment(
                question_id="Is the solution optimal?",
                response_type="probability",
                value=0.95,
                confidence=0.9,
                metadata={"backend": "laya", "model": "typed-decisions"},
            )
        ]


def sample_spec() -> EvaluationSpec:
    return EvaluationSpec.model_validate({
        "evaluation_id": "bridge-test",
        "objective": "Sort integers",
        "collectors": [
            {"id": "build", "type": "build"},
            {"id": "static", "type": "static"},
        ],
        "fitness": {
            "metrics": [
                {
                    "id": "compile_success",
                    "direction": "maximize",
                    "weight": 1.0,
                    "normalization": {"minimum": 0, "maximum": 1},
                }
            ]
        },
        "judge_questions": ["Is the solution optimal?"],
    })


def test_bridge_initialization_with_spec_object():
    spec = sample_spec()
    bridge = OpenEvolveBridge(spec)
    assert bridge.spec.evaluation_id == "bridge-test"


def test_bridge_initialization_with_spec_path(tmp_path: Path):
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(sample_spec().model_dump_json())
    bridge = OpenEvolveBridge(spec_file)
    assert bridge.spec.evaluation_id == "bridge-test"


def test_bridge_workspace_preparation_and_support_map(tmp_path: Path):
    candidate_file = tmp_path / "candidate.py"
    candidate_file.write_text("def solve(): return 42\n")

    support_dir = tmp_path / "tests"
    support_dir.mkdir()
    (support_dir / "test_aux.py").write_text("assert True\n")

    bridge = OpenEvolveBridge(
        sample_spec(),
        support_map={"tests": "tests"},
    )
    bridge.project_root = tmp_path

    work_dir = bridge._prepare_workspace(candidate_file)
    try:
        assert (work_dir / "main.py").exists()
        assert (work_dir / "tests" / "test_aux.py").exists()
    finally:
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


def test_stage1_evaluation_success(tmp_path: Path):
    candidate_file = tmp_path / "valid.py"
    candidate_file.write_text("def sort_list(items):\n    return sorted(items)\n")

    bridge = OpenEvolveBridge(sample_spec())
    res = bridge.evaluate_stage1(candidate_file)
    assert res.metrics["valid"] == 1.0
    assert res.metrics["combined_score"] == 1.0
    assert res.metrics["compile_success"] == 1.0


def test_stage1_evaluation_failure_on_syntax_error(tmp_path: Path):
    candidate_file = tmp_path / "broken.py"
    candidate_file.write_text("def broken(items:\n    return items\n")

    bridge = OpenEvolveBridge(sample_spec())
    res = bridge.evaluate_stage1(candidate_file)
    assert res.metrics["valid"] == 0.0
    assert res.metrics["combined_score"] == 0.0
    assert "failure_reasons" in res.artifacts
    assert "gatekeeper check failed: static-syntax" in res.artifacts["failure_reasons"]


def test_full_evaluation_with_mock_judge(tmp_path: Path):
    candidate_file = tmp_path / "candidate.py"
    candidate_file.write_text("def sort_list(items):\n    return sorted(items)\n")

    judge = MockJudge()
    bridge = OpenEvolveBridge(sample_spec(), judge=judge)
    res = bridge.evaluate(candidate_file)
    assert res.metrics["valid"] == 1.0
    assert res.metrics["combined_score"] == 1.0
    assert res.metrics["compile_success"] == 1.0
    assert res.metrics["compile_success_normalized"] == 1.0
    assert "judge_Is_the_solution_optimal?" in res.artifacts
    assert "prob=0.9500" in res.artifacts["judge_Is_the_solution_optimal?"]


def test_make_evaluator_factory(tmp_path: Path):
    candidate_file = tmp_path / "candidate.py"
    candidate_file.write_text("def sort_list(items):\n    return sorted(items)\n")

    evaluate, evaluate_stage1 = make_evaluator(sample_spec(), judge=MockJudge())
    res1 = evaluate_stage1(candidate_file)
    res2 = evaluate(candidate_file)

    assert res1.metrics["valid"] == 1.0
    assert res2.metrics["valid"] == 1.0
