import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from evaluator.models.candidate import Candidate
from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.spec import EvaluationSpec, JudgeQuestionSpec
from .base import TypedJudge


class JevAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class LayaClientConfig:
    endpoint: str = "https://momen-gpu.tail374b2b.ts.net:8020/predict"
    api_key: str | None = None
    model: str = "typed-decisions"
    timeout_seconds: float = 10.0


class LayaJevClient:
    def __init__(self, config: LayaClientConfig | None = None, request: Callable[..., Any] | None = None):
        self.config = config or LayaClientConfig(api_key=os.getenv("LAYA_API_KEY"))
        self._request = request or self._request_sync

    def _request_sync(self, request: Request, timeout: float) -> bytes:
        with urlopen(request, timeout=timeout) as response:
            return response.read()

    async def predict(self, *, state: str, questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
        if not self.config.api_key:
            raise JevAPIError("LAYA_API_KEY is not configured")
        payload = {
            "model": self.config.model,
            "state": state,
            "questions": questions,
        }
        request = Request(
            self.config.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            raw = await asyncio.to_thread(self._request, request, self.config.timeout_seconds)
        except HTTPError as exc:
            raise JevAPIError(f"Laya API returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise JevAPIError(f"Laya API request failed: {exc}") from exc
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JevAPIError("Laya API returned invalid JSON") from exc
        if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
            raise JevAPIError("Laya API response must contain an answers object")
        return data


class JevJudge(TypedJudge):
    name = "jev"

    def __init__(self, client: LayaJevClient | None = None):
        self.client = client or LayaJevClient()

    @staticmethod
    def _question_payload(question: str | JudgeQuestionSpec) -> tuple[str, dict[str, Any]]:
        if isinstance(question, str):
            return question, {
                "type": "noul",
                "instructions": question,
            }
        payload: dict[str, Any] = {
            "type": question.type,
            "instructions": question.instructions,
        }
        if question.criteria is not None:
            payload["criteria"] = question.criteria
        return question.id, payload

    @staticmethod
    def _state(spec: EvaluationSpec, evidence: list[Evidence], candidate: Candidate | None = None) -> str:
        state: dict[str, Any] = {
            "objective": spec.objective,
            "evaluation_id": spec.evaluation_id,
            "evidence": [
                {
                    "id": item.id,
                    "collector": item.collector,
                    "category": item.category.value,
                    "status": item.status.value,
                    "value": item.value,
                    "unit": item.unit,
                    "confidence": item.confidence,
                    "metadata": item.metadata,
                }
                for item in evidence
            ],
        }
        if candidate is not None:
            try:
                entrypoint = candidate.entrypoint_path()
                if entrypoint.is_file():
                    state["source_code"] = entrypoint.read_text(encoding="utf-8")[:16000]
                    state["candidate_language"] = candidate.language
            except Exception:
                pass
        return json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)

    async def judge(
        self,
        spec: EvaluationSpec,
        evidence: list[Evidence],
        candidate: Candidate | None = None,
    ) -> list[Judgment]:
        if not spec.judge_questions:
            return []

        questions: dict[str, dict[str, Any]] = {}
        question_types: dict[str, str] = {}
        for question in spec.judge_questions:
            qid, qpayload = self._question_payload(question)
            questions[qid] = qpayload
            question_types[qid] = qpayload.get("type", "noul")

        response = await self.client.predict(
            state=self._state(spec, evidence, candidate=candidate),
            questions=questions,
        )
        answers = response["answers"]
        judgments: list[Judgment] = []

        for qid, qtype in question_types.items():
            answer = answers.get(qid)
            if not isinstance(answer, dict):
                raise JevAPIError(f"missing answer for question: {qid}")

            if qtype == "noul":
                if "noul" not in answer:
                    raise JevAPIError(f"missing noul answer for question: {qid}")
                raw_val = answer["noul"]
                if isinstance(raw_val, bool) or not isinstance(raw_val, (int, float)) or not 0 <= float(raw_val) <= 1:
                    raise JevAPIError(f"invalid noul probability for question: {qid}")
                conf = answer.get("confidence", raw_val)
                if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= float(conf) <= 1:
                    raise JevAPIError(f"invalid confidence for question: {qid}")
                judgments.append(
                    Judgment(
                        question_id=qid,
                        response_type="probability",
                        value=float(raw_val),
                        confidence=float(conf),
                        evidence_ids=[e.id for e in evidence],
                        metadata={
                            "backend": "laya",
                            "model": str(response.get("routing", {}).get("model", self.client.config.model)),
                        },
                    )
                )
            elif qtype == "score":
                if "score" not in answer:
                    raise JevAPIError(f"missing score answer for question: {qid}")
                raw_val = answer["score"]
                if isinstance(raw_val, bool) or not isinstance(raw_val, (int, float)):
                    raise JevAPIError(f"invalid score for question: {qid}")
                conf = answer.get("answer_confidence", answer.get("confidence", 1.0))
                if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= float(conf) <= 1:
                    conf = 1.0
                judgments.append(
                    Judgment(
                        question_id=qid,
                        response_type="score",
                        value=float(raw_val),
                        confidence=float(conf),
                        evidence_ids=[e.id for e in evidence],
                        metadata={
                            "backend": "laya",
                            "model": str(response.get("routing", {}).get("model", self.client.config.model)),
                        },
                    )
                )
            elif qtype == "choice":
                if "choice" not in answer:
                    raise JevAPIError(f"missing choice answer for question: {qid}")
                raw_choice = str(answer["choice"])
                conf = answer.get("answer_confidence", answer.get("confidence", 1.0))
                if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= float(conf) <= 1:
                    conf = 1.0
                judgments.append(
                    Judgment(
                        question_id=qid,
                        response_type="choice",
                        value=raw_choice,
                        confidence=float(conf),
                        evidence_ids=[e.id for e in evidence],
                        metadata={
                            "backend": "laya",
                            "model": str(response.get("routing", {}).get("model", self.client.config.model)),
                        },
                    )
                )
            else:
                raise JevAPIError(f"unsupported question type: {qtype}")

        return judgments
