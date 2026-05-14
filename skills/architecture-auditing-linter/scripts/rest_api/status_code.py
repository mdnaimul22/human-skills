"""
Tool: Status Code Appropriate Usage Score
Category: Design Quality
Evaluates whether HTTP status codes are used semantically correctly:
- 200 OK for successful reads
- 201 Created for successful resource creation (POST)
- 204 No Content for successful DELETE / PUT with no body
- 400 Bad Request for validation errors
- 401 Unauthorized for auth failures
- 403 Forbidden for permission errors
- 404 Not Found for missing resources
- 409 Conflict for duplicate/state conflicts
- 422 Unprocessable Entity for semantic validation failures
- 500 Internal Server Error for unexpected server errors
Penalises overuse of 200 for everything, or returning 200 on error.
"""
import re
from typing import Any, List, Tuple
from helpers.tool import Tool

STATUS_CODE_RE = re.compile(
    r'\b(status_code|status|code|http_status)\s*[=:]\s*(\d{3})\b'
    r'|HTTPStatus\.(\w+)'
    r'|response\s*\(\s*.*?status\s*=\s*(\d{3})'
    r'|jsonify\([^)]*\),\s*(\d{3})'
    r'|Response\([^)]*,\s*(\d{3})'
    r'|abort\((\d{3})\)'
    r'|raise\s+HTTP(?:Exception)?\((\d{3})'
    r'|return\s+[^,]+,\s*(\d{3})\b',
    re.IGNORECASE | re.DOTALL,
)

# Contextual signals mapped to appropriate status codes
CONTEXT_SIGNALS: List[Tuple[re.Pattern, List[int]]] = [
    # Creation context → expect 201
    (re.compile(r'\b(create|insert|add|new|\.create\(|db\.add)\b', re.I), [201, 200]),
    # Deletion context → expect 204 or 200
    (re.compile(r'\b(delete|remove|destroy|\.delete\(|db\.delete)\b', re.I), [204, 200]),
    # Auth failure context → expect 401
    (re.compile(r'\b(unauthorized|not authenticated|invalid token|missing token|'
                r'authentication required)\b', re.I), [401]),
    # Permission denied → expect 403
    (re.compile(r'\b(forbidden|permission denied|not allowed|access denied)\b', re.I), [403]),
    # Not found context → expect 404
    (re.compile(r'\b(not found|does not exist|no such|\.first_or_404|get_or_404|'
                r'raise.*404|404)\b', re.I), [404]),
    # Validation error → expect 400 or 422
    (re.compile(r'\b(invalid|validation error|bad request|malformed|'
                r'ValidationError|pydantic|schema)\b', re.I), [400, 422]),
    # Conflict → expect 409
    (re.compile(r'\b(already exists|duplicate|conflict|unique constraint)\b', re.I), [409]),
    # Server error → expect 500
    (re.compile(r'\b(internal server error|unexpected error|traceback|exception caught)\b',
                re.I), [500]),
]

# Codes that are almost always a design smell when over-used
OVERUSED_CODES = {200}

HTTPStatus_MAP = {
    'OK': 200, 'CREATED': 201, 'NO_CONTENT': 204,
    'BAD_REQUEST': 400, 'UNAUTHORIZED': 401, 'FORBIDDEN': 403,
    'NOT_FOUND': 404, 'CONFLICT': 409, 'UNPROCESSABLE_ENTITY': 422,
    'INTERNAL_SERVER_ERROR': 500,
}


def _extract_codes(source_code: str) -> List[int]:
    codes: List[int] = []
    for match in STATUS_CODE_RE.finditer(source_code):
        for group in match.groups():
            if group is None:
                continue
            if group.isdigit():
                codes.append(int(group))
            elif group in HTTPStatus_MAP:
                codes.append(HTTPStatus_MAP[group])
    return codes


def _check_contextual_correctness(source_code: str) -> float:
    """
    For each context signal found, check whether an appropriate code is nearby.
    Returns a ratio of correctly-coded contexts.
    """
    correct = 0
    total = 0

    for signal_pattern, expected_codes in CONTEXT_SIGNALS:
        for match in signal_pattern.finditer(source_code):
            total += 1
            window_start = max(0, match.start() - 100)
            window_end   = min(len(source_code), match.end() + 200)
            window       = source_code[window_start:window_end]

            window_codes = _extract_codes(window)
            if any(c in expected_codes for c in window_codes):
                correct += 1
            elif not window_codes:
                # No status code near the context — partial credit
                correct += 0.4

    return (correct / total) if total > 0 else 0.5


def _penalise_200_overuse(codes: List[int]) -> float:
    """Returns a penalty [0, 0.3] if 200 is the only or dominant code."""
    if not codes:
        return 0.0
    ratio_200 = codes.count(200) / len(codes)
    if ratio_200 == 1.0 and len(codes) > 2:
        return 0.3   # Every response is 200 — strong smell
    if ratio_200 > 0.8:
        return 0.15
    return 0.0


class StatusCodeUsage(Tool):
    def __init__(self):
        super().__init__(
            name="status_code_usage",
            description=(
                "Scores whether HTTP status codes are used semantically correctly in REST API "
                "handlers: checks for appropriate 2xx/4xx/5xx usage in context and penalises "
                "returning 200 for all responses including errors."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        all_codes = _extract_codes(source_code)

        if not all_codes:
            return 0.4  # No explicit status codes — probably missing them

        contextual_score = _check_contextual_correctness(source_code)
        overuse_penalty  = _penalise_200_overuse(all_codes)

        # Bonus for variety of status codes (suggests intentional usage)
        unique_codes = len(set(all_codes))
        variety_bonus = min(0.1 * (unique_codes - 1), 0.2) if unique_codes > 1 else 0.0

        final = contextual_score - overuse_penalty + variety_bonus
        return round(min(max(final, 0.0), 1.0), 4)