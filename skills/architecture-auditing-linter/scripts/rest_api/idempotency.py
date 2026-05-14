"""
Tool: Idempotency Implementation Score
Category: Design Quality

Evaluates whether mutation endpoints handle idempotency correctly.

Sources:
  - Google API Design Guide (AIP-0155: request deduplication)
  - Microsoft REST API Guidelines §Idempotency
  - GitHub REST API conventions (PUT/DELETE idempotent by design)
  - RFC 7231 §4.2.2 (Idempotent Methods)
  - Stripe API design (Idempotency-Key header pattern)

Scoring model (additive, max 1.0):
  0.30 — Idempotency-Key header read and used for deduplication
  0.25 — PUT endpoints designed to be fully idempotent (replace, not append)
  0.20 — Deduplication storage (cache/Redis/DB check for replay)
  0.15 — Conflict detection on duplicate key (409 response)
  0.10 — Idempotency key returned in response header

No-routes baseline: 0.5 (neutral — cannot judge without mutation endpoints)
"""
import re
from typing import Any
from helpers.tool import Tool


# ── Detection patterns ─────────────────────────────────────────────────────────

# Idempotency-Key header read
IDEMPOTENCY_KEY_READ = re.compile(
    r'\b(?:Idempotency-Key|idempotency.?key|idempotencyKey)\b',
    re.IGNORECASE,
)

# PUT endpoint — idempotent by design (full replace, not PATCH append)
PUT_ENDPOINT = re.compile(
    r'@(?:app|router|r)\.\s*put\s*\('
    r'|router\.put\s*\('
    r'|@PutMapping'
    r'|RequestMethod\.PUT',
    re.IGNORECASE,
)

# Deduplication logic: cache/DB check for existing key
DEDUP_LOGIC = re.compile(
    r'\b(?:redis|cache|get_or_create|idempotency_store|'
    r'already_processed|check.*key|key.*exists|'
    r'find.*idempotency|idempotency.*find|'
    r'duplicate.*request|request.*duplicate)\b',
    re.IGNORECASE,
)

# Conflict/duplicate detection (409)
CONFLICT_RESPONSE = re.compile(
    r'\b(?:409|CONFLICT|already_exists|duplicate_key|'
    r'DuplicateKeyError|IntegrityError)\b',
    re.IGNORECASE,
)

# Idempotency key returned in response
KEY_IN_RESPONSE = re.compile(
    r'(?:response\.headers|res\.setHeader|response\.addHeader|'
    r'c\.Header)\s*[\["\(]*(?:Idempotency-Key)',
    re.IGNORECASE,
)

# Mutation endpoints (POST, PUT, PATCH, DELETE)
MUTATION_ENDPOINTS = re.compile(
    r'@(?:app|router|r)\.\s*(?:post|put|patch|delete)\s*\('
    r'|router\.(?:post|put|patch|delete)\s*\('
    r'|@(?:PostMapping|PutMapping|PatchMapping|DeleteMapping)',
    re.IGNORECASE,
)


class IdempotencyImplementation(Tool):
    def __init__(self):
        super().__init__(
            name="idempotency_implementation",
            description=(
                "Scores idempotency practices: checks for Idempotency-Key header handling, "
                "PUT idempotent design, deduplication storage, conflict detection, "
                "and key propagation in responses."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        has_mutations = bool(MUTATION_ENDPOINTS.search(source_code))

        # No mutation endpoints — cannot assess idempotency
        if not has_mutations:
            return 0.5, ["No mutation endpoints (POST/PUT/PATCH/DELETE) detected to evaluate idempotency."]

        score = 0.0
        suggestions = []

        # 1. Idempotency-Key header used (0.30)
        if IDEMPOTENCY_KEY_READ.search(source_code):
            score += 0.30
        else:
            suggestions.append("Accept an 'Idempotency-Key' header in mutation endpoints to allow clients to safely retry requests.")

        # 2. PUT endpoint — idempotent by nature (0.25)
        if PUT_ENDPOINT.search(source_code):
            score += 0.25
        else:
            suggestions.append("Consider using PUT for operations that fully replace a resource (PUT must be strictly idempotent).")

        # 3. Deduplication logic (0.20)
        if DEDUP_LOGIC.search(source_code):
            score += 0.20
        else:
            suggestions.append("Implement deduplication logic (e.g. check DB/Redis if 'Idempotency-Key' was already processed).")

        # 4. 409 Conflict on duplicate (0.15)
        if CONFLICT_RESPONSE.search(source_code):
            score += 0.15
        else:
            suggestions.append("Return HTTP 409 Conflict when a duplicate request or integrity violation occurs.")

        # 5. Key returned in response header (0.10)
        if KEY_IN_RESPONSE.search(source_code):
            score += 0.10
        else:
            suggestions.append("Echo the 'Idempotency-Key' back in the response headers to confirm idempotency handling to the client.")

        return round(min(max(score, 0.0), 1.0), 4), suggestions
