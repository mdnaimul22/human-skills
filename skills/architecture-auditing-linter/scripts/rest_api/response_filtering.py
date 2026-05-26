"""
Tool: Response Field Filtering Score
Category: Design Quality / Performance

Evaluates whether APIs support sparse fieldsets and field projection.

Sources:
  - Google API Design Guide (AIP-0157: partial responses, ?fields= param)
  - Microsoft REST API Guidelines (§7.6 field selection, $select)
  - GitHub REST API conventions (custom media types, field filtering)
  - OData protocol (field projection, $select)
  - GraphQL design principles (ask for what you need)

Scoring model (additive, max 1.0):
  0.30 — ?fields= or ?$select= query parameter supported
  0.25 — Dynamic field selection applied to serializer/response
  0.20 — List endpoints use projection (not returning all fields)
  0.15 — Response schema enforces field subset (ResponseModel/DTO)
  0.10 — Default field set documented / limited in list responses

No-list-endpoint baseline: 0.5 (neutral — cannot assess without GET list)
"""
import re
from typing import Any
from helpers.tool import Tool


# ── Detection patterns ─────────────────────────────────────────────────────────

# ?fields= or ?$select= query param read
FIELDS_PARAM = re.compile(
    r'\b(?:fields|select|\$select|field_set|fieldset|sparse)\b'
    r'\s*[=:]\s*(?:request|query|params|req\.query)',
    re.IGNORECASE,
)

# fields= in query param definition (FastAPI, Flask)
FIELDS_QUERY_DEF = re.compile(
    r'(?:fields|select|\$select)\s*[=:]\s*(?:Query\(|Optional\[|str\b)',
    re.IGNORECASE,
)

# Dynamic field selection applied to ORM/serializer
DYNAMIC_FIELD_SELECTION = re.compile(
    r'\.only\s*\(|\.values\s*\(|\.values_list\s*\('
    r'|filter_fields|select_fields|project\s*\('
    r'|\bfields_filter\b|\bfield_projection\b'
    r'|serializer.*fields.*request'
    r'|\$project\s*:\s*\{',
    re.IGNORECASE,
)

# Response model / DTO enforcing a field subset
RESPONSE_MODEL = re.compile(
    r'response_model\s*=\s*\w+'
    r'|class\s+\w+(?:Response|Out|DTO|Schema|View)\s*[:\(]'
    r'|@JsonView|@ResponseBody.*\w+DTO',
    re.IGNORECASE,
)

# List endpoint (GET returning multiple items)
LIST_ENDPOINT = re.compile(
    r'@(?:app|router|r)\.\s*get\s*\('
    r'|router\.get\s*\('
    r'|@GetMapping\s*\(',
    re.IGNORECASE,
)

# Projection in list — using .only() or SELECT specific cols
LIST_PROJECTION = re.compile(
    r'\.only\s*\(|\.values\s*\(|SELECT\s+\w+(?:\s*,\s*\w+)+\s+FROM'
    r'|\$project|\bproject\s*=',
    re.IGNORECASE,
)

# Default limited fields documented or set
DEFAULT_FIELDS = re.compile(
    r'default_fields\s*=|DEFAULT_FIELDS\s*='
    r'|default_list_fields|COMPACT_FIELDS'
    r'|X-Fields|Accept.*application/json.*fields',
    re.IGNORECASE,
)


class ResponseFieldFiltering(Tool):
    def __init__(self):
        super().__init__(
            name="response_field_filtering",
            description=(
                "Scores response field filtering implementation: checks for ?fields= query param "
                "support, dynamic field selection on serializers, response DTO enforcement, "
                "and list endpoint projection patterns (Google AIP-0157)."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        has_list = bool(LIST_ENDPOINT.search(source_code))

        # No list endpoints — neutral
        if not has_list:
            return 0.5, []

        score = 0.0
        suggestions = []

        # 1. ?fields= / ?$select= query param (0.30)
        if FIELDS_PARAM.search(source_code) or FIELDS_QUERY_DEF.search(source_code):
            score += 0.30
        else:
            suggestions.append("Support sparse fieldsets (e.g., ?fields=id,name) to allow clients to request only needed data.")

        # 2. Dynamic field selection (0.25)
        if DYNAMIC_FIELD_SELECTION.search(source_code):
            score += 0.25
        else:
            suggestions.append("Implement dynamic field projection at the database or serializer level to avoid fetching unused columns.")

        # 3. List endpoint uses projection (0.20)
        if LIST_PROJECTION.search(source_code):
            score += 0.20
        else:
            suggestions.append("Ensure list endpoints do not use 'SELECT *' equivalent; query only the necessary fields.")

        # 4. Response model / DTO restricts fields (0.15)
        if RESPONSE_MODEL.search(source_code):
            score += 0.15
        else:
            suggestions.append("Use Response Models / DTOs to enforce the exact schema returned, avoiding database-model leakage.")

        # 5. Default field set limited (0.10)
        if DEFAULT_FIELDS.search(source_code):
            score += 0.10

        if score < 0.65 and not suggestions:
            suggestions.append("Review Google API Design Guide (AIP-0157) on Partial Responses to improve response performance.")

        return round(min(max(score, 0.0), 1.0), 4), suggestions
