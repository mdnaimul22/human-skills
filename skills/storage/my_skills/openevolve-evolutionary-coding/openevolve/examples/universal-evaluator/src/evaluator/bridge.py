from __future__ import annotations

import asyncio
from collections.abc import Iterable
import os
from pathlib import Path
import shutil
import tempfile

from evaluator.collectors.registry import CollectorRegistry
from evaluator.engine import EvaluationEngine
from evaluator.judges.base import TypedJudge
from evaluator.judges.jev import JevJudge, LayaClientConfig, LayaJevClient
from evaluator.metrics.registry import MetricRegistry
from evaluator.models.candidate import Candidate
from evaluator.models.evidence import Evidence, EvidenceStatus
from evaluator.models.run import EvaluationRun
from evaluator.models.spec import EvaluationSpec
from evaluator.sandbox.base import Sandbox

try:
    from openevolve.evaluation_result import EvaluationResult
except ImportError:
    EvaluationResult = None


def _build_judge() -> JevJudge | None:
    api_key = os.getenv("LAYA_API_KEY")
    if not api_key:
        return None
    config = LayaClientConfig(
        endpoint=os.getenv("LAYA_ENDPOINT", "https://momen-gpu.tail374b2b.ts.net:8020/predict"),
        api_key=api_key,
        model=os.getenv("LAYA_MODEL", "typed-decisions"),
        timeout_seconds=float(os.getenv("LAYA_TIMEOUT", "10.0")),
    )
    return JevJudge(LayaJevClient(config))


def _derive_suggestion(failures: list[str], evidence: list[Evidence]) -> str:
    parts: list[str] = []
    for failure in failures:
        if "constraint failed" in failure:
            parts.append(f"Hard constraint violation: {failure}")
        elif "missing metric" in failure:
            parts.append(f"Metric unavailable: {failure}")
        elif "normalization failed" in failure:
            parts.append(f"Normalization error: {failure}")
    for ev in evidence:
        if ev.status == EvidenceStatus.FAILED:
            stderr = ev.metadata.get("stderr", "")
            if stderr:
                parts.append(f"[{ev.collector}] {str(stderr)[:500]}")
    return "\n".join(parts) if parts else "Review failure reasons and evidence above."


def _run_to_openevolve(run: EvaluationRun) -> EvaluationResult | dict[str, Any]:
    fitness = run.fitness
    combined = fitness.fitness if fitness else 0.0
    metrics: dict[str, float] = {"combined_score": float(combined)}
    artifacts: dict[str, str] = {}

    if fitness:
        metrics["valid"] = 1.0 if fitness.valid else 0.0
        for mr in fitness.metrics:
            metrics[mr.metric_id] = float(mr.raw_value)
            metrics[f"{mr.metric_id}_normalized"] = float(mr.normalized_value)
        if fitness.failure_reasons:
            artifacts["failure_reasons"] = "\n".join(fitness.failure_reasons)
            artifacts["suggestion"] = _derive_suggestion(fitness.failure_reasons, run.evidence)

    for ev in run.evidence:
        if ev.status == EvidenceStatus.FAILED:
            stderr = ev.metadata.get("stderr", "")
            stdout = ev.metadata.get("stdout", "")
            if stderr:
                artifacts[f"{ev.id}_stderr"] = str(stderr)[:4000]
            if stdout:
                artifacts[f"{ev.id}_stdout"] = str(stdout)[:4000]

    for j in run.judgments:
        label = j.question_id[:60].replace(" ", "_")
        prefix = "prob" if j.response_type == "probability" else j.response_type
        if isinstance(j.value, (int, float)):
            artifacts[f"judge_{label}"] = f"{prefix}={j.value:.4f} conf={j.confidence:.4f}"
        else:
            artifacts[f"judge_{label}"] = f"{prefix}={j.value} conf={j.confidence:.4f}"

    if EvaluationResult is not None:
        return EvaluationResult(metrics=metrics, artifacts=artifacts)
    return {"metrics": metrics, "artifacts": artifacts}


class OpenEvolveBridge:
    def __init__(
        self,
        spec: EvaluationSpec | str | Path,
        support_map: dict[str, str] | None = None,
        entrypoint: str = "main.py",
        collector_registry: CollectorRegistry | None = None,
        metric_registry: MetricRegistry | None = None,
        judge: TypedJudge | None = None,
        stage1_types: Iterable[str] | None = None,
        sandbox: Sandbox | None = None,
    ):
        if isinstance(spec, EvaluationSpec):
            self.spec = spec
            self.project_root = Path.cwd()
        else:
            spec_path = Path(spec).resolve()
            self.spec = EvaluationSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
            self.project_root = spec_path.parent

        self.support_map = dict(support_map or {})
        self.entrypoint = entrypoint
        self.collector_registry = collector_registry or CollectorRegistry.canonical()
        self.metric_registry = metric_registry or MetricRegistry.canonical()
        self.judge = judge if judge is not None else _build_judge()
        self.stage1_types = frozenset(stage1_types or ("build", "static"))
        self.sandbox = sandbox

    def _prepare_workspace(self, program_path: str | Path) -> Path:
        work_dir = Path(tempfile.mkdtemp(prefix="ue_"))
        shutil.copy2(program_path, work_dir / self.entrypoint)
        for src_rel, dst_rel in self.support_map.items():
            src = self.project_root / src_rel
            dst = work_dir / dst_rel
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            elif src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        return work_dir

    def _candidate(self, work_dir: Path) -> Candidate:
        return Candidate(
            candidate_id=work_dir.name,
            root=work_dir,
            entrypoint=self.entrypoint,
            language="python",
        )

    async def evaluate_async(self, program_path: str | Path) -> EvaluationResult | dict[str, Any]:
        work_dir = self._prepare_workspace(program_path)
        try:
            candidate = self._candidate(work_dir)
            engine = EvaluationEngine(
                collector_registry=self.collector_registry,
                metric_registry=self.metric_registry,
                judge=self.judge,
                sandbox=self.sandbox,
            )
            run = await engine.evaluate(candidate, self.spec)
            return _run_to_openevolve(run)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def evaluate(self, program_path: str | Path) -> EvaluationResult | dict[str, Any]:
        return asyncio.run(self.evaluate_async(program_path))

    async def evaluate_stage1_async(self, program_path: str | Path) -> EvaluationResult | dict[str, Any]:
        work_dir = self._prepare_workspace(program_path)
        try:
            if self.sandbox is not None:
                setattr(self.spec, "_sandbox", self.sandbox)
            candidate = self._candidate(work_dir)
            stage1_configs = [c for c in self.spec.collectors if c.type in self.stage1_types]
            if not stage1_configs:
                metrics = {"combined_score": 1.0, "valid": 1.0}
                if EvaluationResult is not None:
                    return EvaluationResult(metrics=metrics, artifacts={})
                return {"metrics": metrics, "artifacts": {}}

            collected: list[Evidence] = []
            failures: list[str] = []
            for cfg in stage1_configs:
                if not cfg.enabled:
                    continue
                collector = self.collector_registry.create(cfg.type)
                try:
                    items = await collector.collect(candidate, self.spec)
                    collected.extend(items)
                except Exception as exc:
                    failures.append(f"collector {collector.name} failed: {exc}")

            failed_items = [item for item in collected if item.status == EvidenceStatus.FAILED]
            for item in failed_items:
                failures.append(f"gatekeeper check failed: {item.id}")

            metrics = {
                "combined_score": 0.0 if failures else 1.0,
                "valid": 0.0 if failures else 1.0,
            }
            artifacts: dict[str, str] = {}
            if failures:
                artifacts["failure_reasons"] = "\n".join(failures)
                artifacts["suggestion"] = _derive_suggestion(failures, collected)

            for ev in collected:
                if ev.status == EvidenceStatus.FAILED:
                    stderr = ev.metadata.get("stderr", "")
                    stdout = ev.metadata.get("stdout", "")
                    if stderr:
                        artifacts[f"{ev.id}_stderr"] = str(stderr)[:4000]
                    if stdout:
                        artifacts[f"{ev.id}_stdout"] = str(stdout)[:4000]

            for metric in self.spec.fitness.metrics:
                try:
                    derived = self.metric_registry.derive(metric, collected, [])
                    metrics[metric.id] = float(derived.value)
                except Exception:
                    pass

            if EvaluationResult is not None:
                return EvaluationResult(metrics=metrics, artifacts=artifacts)
            return {"metrics": metrics, "artifacts": artifacts}
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def evaluate_stage1(self, program_path: str | Path) -> EvaluationResult | dict[str, Any]:
        return asyncio.run(self.evaluate_stage1_async(program_path))


def make_evaluator(
    spec: EvaluationSpec | str | Path,
    support_map: dict[str, str] | None = None,
    entrypoint: str = "main.py",
    judge: TypedJudge | None = None,
    sandbox: Sandbox | None = None,
):
    bridge = OpenEvolveBridge(spec, support_map=support_map, entrypoint=entrypoint, judge=judge, sandbox=sandbox)
    return bridge.evaluate, bridge.evaluate_stage1
