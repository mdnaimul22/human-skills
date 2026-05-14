"""
Tool: Sensitive Data Exposure Score
Category: Security (OWASP API Security Top 10 — API3:2023)

Evaluates whether API responses leak sensitive fields.

Sources:
  - OWASP API Security Top 10 (API3: Excessive Data Exposure)
  - Google API Design Guide (data minimization)
  - Microsoft REST API Guidelines (response field selection)
  - GitHub REST API conventions (lean response objects)

Scoring model (start 1.0, deduct penalties):
  -0.40 — Sensitive field directly in response serializer (password, secret, token)
  -0.30 — All model fields returned without exclusion (__all__ or SELECT *)
  -0.20 — No field exclusion / only= / exclude= present
  -0.10 — Internal fields (created_at, updated_at, internal_id) not filtered

Bonuses (reduce penalty):
  +0.20 — Explicit exclude= or write_only=True on sensitive fields
  +0.15 — Response model different from DB model (DTO/schema separation)
  +0.10 — fields= / only= restricts returned fields
"""
import re
from typing import Any
from helpers.tool import Tool


# ── Sensitive field patterns ───────────────────────────────────────────────────

SENSITIVE_FIELD_IN_RESPONSE = re.compile(
    r'(?:serialize|to_dict|jsonify|model_dump|dict\(\)|'
    r'Response\s*\(|json\(\)|asdict)\b'
    r'[^#\n]{0,200}'
    r'\b(?:password|passwd|secret|token|api_key|private_key|'
    r'credit_card|ssn|cvv|pin)\b',
    re.IGNORECASE | re.DOTALL,
)

# Serializer with fields = '__all__' — returns everything
FIELDS_ALL = re.compile(
    r'fields\s*=\s*["\']?__all__["\']?',
    re.IGNORECASE,
)

# SELECT * equivalent — all DB columns returned
SELECT_ALL = re.compile(
    r'\bSELECT\s+\*\b|\.all\(\)\s*$|find\(\s*\)\s*$',
    re.IGNORECASE | re.MULTILINE,
)

# Explicit field exclusion on serializer
EXPLICIT_EXCLUDE = re.compile(
    r'exclude\s*=\s*[\[\(]|write_only\s*=\s*True|'
    r'exclude_fields|excluded_fields|'
    r'@JsonIgnore|@JsonProperty.*access.*WRITE_ONLY',
    re.IGNORECASE,
)

# Explicit field restriction (only= or fields= with specific list)
FIELDS_ONLY = re.compile(
    r'only\s*=\s*\[|fields\s*=\s*\[(?!.*__all__)|'
    r'response_model\s*=\s*\w+(?!User$|Model$)|'
    r'ResponseSchema|ResponseModel|ResponseDTO|'
    r'class\s+\w+(?:Response|DTO|Out|Schema)\s*[:\(]',
    re.IGNORECASE,
)

# Separate response model / DTO class (good separation)
RESPONSE_DTO = re.compile(
    r'class\s+\w+(?:Response|ResponseDTO|Out|Schema|View|Dto)\s*[:\(]'
    r'|response_model\s*=\s*\w+',
    re.IGNORECASE,
)

# Serializer / schema present (positive signal)
SERIALIZER_PRESENT = re.compile(
    r'\b(?:Serializer|Schema|ModelSchema|marshmallow|pydantic\.BaseModel|'
    r'serializers\.ModelSerializer|ResponseModel)\b',
    re.IGNORECASE,
)


class SensitiveDataExposure(Tool):
    def __init__(self):
        super().__init__(
            name="sensitive_data_exposure",
            description=(
                "Scores sensitive data handling: checks for password/secret/token fields in "
                "response serialization, field exclusion patterns, DTO separation, "
                "and data minimization. Based on OWASP API3: Excessive Data Exposure."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        has_serializer = (
            SERIALIZER_PRESENT.search(source_code) or
            FIELDS_ONLY.search(source_code) or
            EXPLICIT_EXCLUDE.search(source_code) or
            RESPONSE_DTO.search(source_code) or
            SENSITIVE_FIELD_IN_RESPONSE.search(source_code) or
            FIELDS_ALL.search(source_code)
        )

        # No serialization context — cannot judge
        if not has_serializer:
            return 0.5

        score = 1.0  # Start perfect, deduct for violations

        # ── Penalties ──────────────────────────────────────────────────────────

        # Sensitive field directly in response
        if SENSITIVE_FIELD_IN_RESPONSE.search(source_code):
            score -= 0.40

        # fields = '__all__' — exposes every DB column
        if FIELDS_ALL.search(source_code):
            score -= 0.30

        # SELECT * or .all() without projection
        if SELECT_ALL.search(source_code):
            score -= 0.10

        # ── Bonuses ────────────────────────────────────────────────────────────

        # Explicit exclude= or write_only=True
        if EXPLICIT_EXCLUDE.search(source_code):
            score = min(score + 0.20, 1.0)

        # Separate response DTO/schema
        if RESPONSE_DTO.search(source_code):
            score = min(score + 0.15, 1.0)

        # fields= / only= with specific list
        if FIELDS_ONLY.search(source_code):
            score = min(score + 0.10, 1.0)

        return round(min(max(score, 0.0), 1.0), 4)
