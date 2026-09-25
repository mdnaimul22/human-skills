from dataclasses import dataclass

from .models.candidate import Candidate
from .models.evidence import Evidence
from .models.spec import EvaluationSpec


@dataclass(frozen=True)
class EvidenceValidationError:
    evidence_id: str
    reason: str


class EvidenceValidator:
    """Validates collector output before evidence can influence metrics."""

    def validate(
        self,
        evidence: list[Evidence],
        *,
        candidate: Candidate,
        spec: EvaluationSpec,
        run_id: str,
        candidate_fingerprint: str,
        spec_hash: str,
        collector_versions: dict[str, str],
    ) -> list[EvidenceValidationError]:
        errors: list[EvidenceValidationError] = []
        seen: set[str] = set()
        for item in evidence:
            if item.id in seen:
                errors.append(EvidenceValidationError(item.id, "duplicate evidence id"))
            seen.add(item.id)

            p = item.provenance
            if p.candidate_id != candidate.candidate_id:
                errors.append(EvidenceValidationError(item.id, "candidate_id provenance mismatch"))
            if p.candidate_version != candidate.version:
                errors.append(EvidenceValidationError(item.id, "candidate_version provenance mismatch"))
            if item.collector not in collector_versions:
                errors.append(EvidenceValidationError(item.id, f"unknown collector: {item.collector}"))
            else:
                expected = collector_versions[item.collector]
                if p.collector_version != expected:
                    errors.append(EvidenceValidationError(item.id, "collector_version provenance mismatch"))

            if p.run_id is not None and p.run_id != run_id:
                errors.append(EvidenceValidationError(item.id, "run_id provenance mismatch"))
            if p.evaluation_id is not None and p.evaluation_id != spec.evaluation_id:
                errors.append(EvidenceValidationError(item.id, "evaluation_id provenance mismatch"))
            if p.spec_hash is not None and p.spec_hash != spec_hash:
                errors.append(EvidenceValidationError(item.id, "spec_hash provenance mismatch"))
            if p.candidate_fingerprint is not None and p.candidate_fingerprint != candidate_fingerprint:
                errors.append(EvidenceValidationError(item.id, "candidate_fingerprint provenance mismatch"))

            if item.status.value == "passed" and item.confidence <= 0:
                errors.append(EvidenceValidationError(item.id, "passed evidence must have positive confidence"))

        return errors
