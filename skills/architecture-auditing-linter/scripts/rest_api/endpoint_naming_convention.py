import re
import ast
from typing import Any, List
from helpers.tool import Tool


VERB_PATTERNS = re.compile(
    r'\b(get|post|put|delete|create|update|fetch|retrieve|add|remove|'
    r'list|find|search|load|save|make|do|run|check|handle|process)\b',
    re.IGNORECASE,
)

CAMEL_CASE_PATTERN = re.compile(r'[a-z][A-Z]')
SNAKE_CASE_PATTERN = re.compile(r'[a-zA-Z]_[a-zA-Z]')

COMMON_PLURAL_SUFFIXES = ('s', 'es', 'ies')

ROUTE_DECORATORS = {
    'flask':    re.compile(r'@(?:\w+\.)?route\(["\']([^"\']+)["\']'),
    'fastapi':  re.compile(r'@(?:\w+\.)?(get|post|put|delete|patch)\(["\']([^"\']+)["\']'),
    'django':   re.compile(r'path\(["\']([^"\']+)["\']'),
    'express':  re.compile(r'(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'),
}


def _extract_endpoints(source_code: str) -> List[str]:
    endpoints: List[str] = []
    for name, pattern in ROUTE_DECORATORS.items():
        matches = pattern.findall(source_code)
        for match in matches:
            path = match if isinstance(match, str) else match[-1]
            endpoints.append(path)
    return list(set(endpoints))


def _score_single_endpoint(path: str) -> float:
    score = 1.0
    deductions = []

    segments = [s for s in path.split('/') if s and not s.startswith('{') and not s.startswith(':')]

    if not segments:
        return 1.0

    # Check for verbs in path
    for segment in segments:
        if VERB_PATTERNS.match(segment):
            deductions.append(0.25)

    # Check for camelCase (should use kebab-case)
    for segment in segments:
        if CAMEL_CASE_PATTERN.search(segment):
            deductions.append(0.2)

    # Check for snake_case (should use kebab-case)
    for segment in segments:
        if SNAKE_CASE_PATTERN.search(segment):
            deductions.append(0.1)

    # Check plural nouns for collection endpoints
    if segments:
        last = segments[-1]
        is_plural = any(last.endswith(s) for s in COMMON_PLURAL_SUFFIXES)
        if not is_plural and len(last) > 2:
            deductions.append(0.15)

    # Penalise excessive nesting depth (> 3 levels is hard to maintain)
    real_depth = len([s for s in path.split('/') if s])
    if real_depth > 4:
        deductions.append(0.1 * (real_depth - 4))

    # Uppercase letters
    if any(c.isupper() for c in path.replace('{', '').replace('}', '')):
        deductions.append(0.2)

    total_deduction = sum(deductions)
    return max(0.0, score - total_deduction)


class EndpointNamingConvention(Tool):
    def __init__(self):
        super().__init__(
            name="endpoint_naming_convention",
            description=(
                "Scores REST API endpoint naming conventions: checks for lowercase kebab-case paths, "
                "plural resource nouns, absence of verbs, and sensible nesting depth."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        endpoints = _extract_endpoints(source_code)

        if not endpoints:
            # Fall back to heuristic: look for string literals that look like paths
            path_literals = re.findall(r'["\'](/[a-zA-Z0-9_\-/{}/]+)["\']', source_code)
            endpoints = [p for p in path_literals if len(p) > 1]

        if not endpoints:
            return 0.5  # Neutral — no endpoints found to evaluate

        scores = [_score_single_endpoint(ep) for ep in endpoints]
        return round(sum(scores) / len(scores), 4)