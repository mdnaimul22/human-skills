import hashlib
import inspect
import json
from pathlib import Path
from uuid import uuid4

from .evidence_validator import EvidenceValidator
from .fitness.aggregate import aggregate
from .fitness.metrics import MetricDerivationError, derive_metric
from .metrics.registry import MetricRegistry
from .collectors.registry import CollectorRegistry
from .models.evidence import EvidenceProvenance
from .models.run import EvaluationRun


def _hash_spec(spec) -> str:
    payload = json.dumps(spec.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _fingerprint_candidate(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class EvaluationEngine:
    def __init__(self, collectors=None, judge=None, metric_registry=None, collector_registry=None, sandbox=None):
        self.collector_registry = collector_registry or CollectorRegistry.canonical()
        self.collectors = collectors
        self.judge = judge
        self.metric_registry = metric_registry or MetricRegistry.canonical()
        self.evidence_validator = EvidenceValidator()
        self.sandbox = sandbox

    async def evaluate(self, candidate, spec):
        if self.sandbox is not None:
            setattr(spec, "_sandbox", self.sandbox)
        run = EvaluationRun(
            evaluation_id=spec.evaluation_id,
            run_id=str(uuid4()),
            started_at=EvaluationRun.now(),
            candidate=candidate,
        )
        spec_hash = _hash_spec(spec)
        candidate_fingerprint = _fingerprint_candidate(candidate.root)
        if self.collectors is not None:
            active_collectors = list(self.collectors)
        else:
            active_collectors = self.collector_registry.resolve(spec.collectors)

        collector_versions = {collector.name: collector.version for collector in active_collectors}

        collected = []
        collection_failures = []
        for collector in active_collectors:
            try:
                items = await collector.collect(candidate, spec)
            except Exception as exc:
                collection_failures.append(f"collector {collector.name} failed: {exc}")
                continue
            errors = self.evidence_validator.validate(
                items, candidate=candidate, spec=spec, run_id=run.run_id,
                candidate_fingerprint=candidate_fingerprint, spec_hash=spec_hash,
                collector_versions=collector_versions,
            )
            if errors:
                collection_failures.extend(f"evidence {e.evidence_id}: {e.reason}" for e in errors)
                continue
            for item in items:
                item.provenance = item.provenance.model_copy(update={
                    "evaluation_id": spec.evaluation_id,
                    "run_id": run.run_id,
                    "spec_hash": spec_hash,
                    "candidate_fingerprint": candidate_fingerprint,
                })
            collected.extend(items)
        run.evidence = collected

        judge_failures: list[str] = []
        if self.judge:
            try:
                params = inspect.signature(self.judge.judge).parameters
                if "candidate" in params or any(p.kind == p.VAR_KEYWORD for p in params.values()):
                    run.judgments.extend(await self.judge.judge(spec, run.evidence, candidate=candidate))
                else:
                    run.judgments.extend(await self.judge.judge(spec, run.evidence))
            except Exception as exc:
                judge_failures.append(f"judge {getattr(self.judge, 'name', 'unknown')} failed: {exc}")

        values: dict[str, float] = {}
        evidence_ids: dict[str, list[str]] = {}
        judgment_ids: dict[str, list[str]] = {}
        derivation_failures: list[str] = []
        for metric in spec.fitness.metrics:
            try:
                derived = self.metric_registry.derive(metric, run.evidence, run.judgments)
                values[metric.id] = derived.value
                evidence_ids[metric.id] = derived.evidence_ids
                judgment_ids[metric.id] = derived.judgment_ids
            except (ValueError, TypeError, MetricDerivationError) as exc:
                derivation_failures.append(f"metric {metric.id}: {exc}")

        run.fitness = aggregate(spec.fitness, values, evidence_ids, judgment_ids)
        failures = collection_failures + derivation_failures + judge_failures
        if failures:
            run.fitness.valid = False
            run.fitness.fitness = 0
            run.fitness.failure_reasons = failures + run.fitness.failure_reasons
        run.finished_at = EvaluationRun.now()
        return run
