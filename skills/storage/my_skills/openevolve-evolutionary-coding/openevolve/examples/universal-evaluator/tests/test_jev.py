import json

import pytest

from evaluator.judges.jev import JevAPIError, LayaClientConfig, LayaJevClient, JevJudge
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceProvenance, EvidenceStatus
from evaluator.models.spec import EvaluationSpec


def spec() -> EvaluationSpec:
    return EvaluationSpec.model_validate({
        "evaluation_id": "jev-test",
        "objective": "Evaluate candidate correctness",
        "fitness": {"metrics": [{
            "id": "correctness", "source": {"collector": "test", "category": "correctness"},
            "direction": "maximize", "weight": 1, "minimum": 0, "maximum": 1,
        }]},
        "judge_questions": ["Is the candidate semantically correct?"],
    })


def evidence() -> list[Evidence]:
    return [Evidence(
        id="e1", collector="test", category=EvidenceCategory.CORRECTNESS,
        status=EvidenceStatus.PASSED, value=1, confidence=1, duration_ms=1,
        provenance=EvidenceProvenance(candidate_id="c1", collector_version="1.0"),
    )]


def fake_request(request, timeout):
    body = json.loads(request.data.decode())
    assert body["model"] == "typed-decisions"
    assert body["questions"]["Is the candidate semantically correct?"]["type"] == "noul"
    return json.dumps({
        "model": "laya-rl-agent",
        "answers": {"Is the candidate semantically correct?": {"noul": 0.92, "confidence": 0.88}},
        "routing": {"model": "typed-decisions"},
    }).encode()


@pytest.mark.asyncio
async def test_jev_parses_typed_laya_response():
    client = LayaJevClient(LayaClientConfig(api_key="test"), request=fake_request)
    judgments = await JevJudge(client).judge(spec(), evidence())
    assert judgments[0].value == 0.92
    assert judgments[0].confidence == 0.88
    assert judgments[0].metadata["model"] == "typed-decisions"


@pytest.mark.asyncio
async def test_jev_requires_api_key():
    client = LayaJevClient(LayaClientConfig(api_key=None))
    with pytest.raises(JevAPIError, match="LAYA_API_KEY"):
        await client.predict(state="x", questions={"q": {"type": "noul", "instructions": "x"}})


def judgment_metric_spec() -> EvaluationSpec:
    return EvaluationSpec.model_validate({
        "evaluation_id": "jev-fitness-test",
        "objective": "Semantic evaluation",
        "fitness": {"metrics": [{
            "id": "semantic",
            "source": {"kind": "judgment", "question_id": "Is the candidate semantically correct?"},
            "direction": "maximize", "weight": 1, "minimum": 0, "maximum": 1,
        }]},
        "judge_questions": ["Is the candidate semantically correct?"],
    })


@pytest.mark.asyncio
async def test_jev_judgment_can_become_fitness_metric():
    client = LayaJevClient(LayaClientConfig(api_key="test"), request=fake_request)
    judgments = await JevJudge(client).judge(judgment_metric_spec(), evidence())
    from evaluator.fitness.metrics import derive_metric
    value, ids = derive_metric(judgment_metric_spec().fitness.metrics[0], evidence(), judgments)
    assert value == 0.92
    assert ids == ["Is the candidate semantically correct?"]

@pytest.mark.asyncio
async def test_judgment_metric_is_normalized_for_fitness():
    from evaluator.fitness.aggregate import aggregate
    from evaluator.fitness.metrics import derive_metric

    s = judgment_metric_spec()
    client = LayaJevClient(LayaClientConfig(api_key="test"), request=fake_request)
    judgments = await JevJudge(client).judge(s, evidence())
    metric = s.fitness.metrics[0]
    value, ids = derive_metric(metric, evidence(), judgments)
    result = aggregate(s.fitness, {metric.id: value}, {}, {metric.id: ids})
    assert result.valid is True
    assert result.fitness == 0.92
    assert result.metrics[0].judgment_ids == ["Is the candidate semantically correct?"]


@pytest.mark.asyncio
async def test_jev_injects_candidate_source_code_into_state(tmp_path):
    from evaluator.models.candidate import Candidate

    code_file = tmp_path / "solution.py"
    code_file.write_text("def solve(): return 42", encoding="utf-8")
    cand = Candidate(
        candidate_id="c_test",
        root=tmp_path,
        entrypoint="solution.py",
        language="python",
    )

    captured_state = {}

    def capture_request(req, timeout):
        payload = json.loads(req.data.decode())
        captured_state.update(json.loads(payload["state"]))
        return json.dumps({
            "model": "laya-rl-agent",
            "answers": {"Is the candidate semantically correct?": {"noul": 0.95, "confidence": 0.95}},
            "routing": {"model": "typed-decisions"},
        }).encode()

    client = LayaJevClient(LayaClientConfig(api_key="test"), request=capture_request)
    await JevJudge(client).judge(spec(), evidence(), candidate=cand)
    assert captured_state.get("source_code") == "def solve(): return 42"
    assert captured_state.get("candidate_language") == "python"


@pytest.mark.asyncio
async def test_jev_handles_choice_and_score_questions():
    from evaluator.models.spec import JudgeQuestionSpec

    structured_spec = EvaluationSpec.model_validate({
        "evaluation_id": "structured-jev-test",
        "objective": "Test typed questions",
        "fitness": {"metrics": [{
            "id": "quality",
            "source": {"kind": "judgment", "question_id": "code_score"},
            "direction": "maximize", "weight": 1, "minimum": 0, "maximum": 5,
        }]},
        "judge_questions": [
            JudgeQuestionSpec(
                id="algo_family",
                type="choice",
                instructions="Which algorithm is used?",
                criteria={"timsort": "builtin sort", "bubble": "nested loop"},
            ),
            JudgeQuestionSpec(
                id="code_score",
                type="score",
                instructions="Rate efficiency from 1 to 5",
                criteria=["1", "2", "3", "4", "5"],
            ),
            "is_fast",
        ],
    })

    def fake_structured_request(req, timeout):
        payload = json.loads(req.data.decode())
        assert payload["questions"]["algo_family"]["type"] == "choice"
        assert payload["questions"]["code_score"]["type"] == "score"
        assert payload["questions"]["is_fast"]["type"] == "noul"
        return json.dumps({
            "model": "laya-rl-agent",
            "answers": {
                "algo_family": {"type": "choice", "choice": "timsort", "answer_confidence": 0.85},
                "code_score": {"type": "score", "score": 4.5, "answer_confidence": 0.90},
                "is_fast": {"type": "noul", "noul": 0.98, "confidence": 0.95},
            },
            "routing": {"model": "typed-decisions"},
        }).encode()

    client = LayaJevClient(LayaClientConfig(api_key="test"), request=fake_structured_request)
    judgments = await JevJudge(client).judge(structured_spec, evidence())
    assert len(judgments) == 3
    algo_j = next(j for j in judgments if j.question_id == "algo_family")
    assert algo_j.response_type == "choice"
    assert algo_j.value == "timsort"
    assert algo_j.confidence == 0.85

    score_j = next(j for j in judgments if j.question_id == "code_score")
    assert score_j.response_type == "score"
    assert score_j.value == 4.5
    assert score_j.confidence == 0.90

    fast_j = next(j for j in judgments if j.question_id == "is_fast")
    assert fast_j.response_type == "probability"
    assert fast_j.value == 0.98

