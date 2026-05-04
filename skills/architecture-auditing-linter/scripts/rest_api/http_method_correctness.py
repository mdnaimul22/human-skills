import re
from typing import Any, Dict, List, Tuple
from helpers.tool import Tool

MUTATION_SIGNALS = re.compile(
    r'\b(insert|update|delete|remove|save|create|drop|truncate|execute|commit|'
    r'db\.add|db\.delete|session\.add|session\.delete|\.save\(\)|\.delete\(\)|'
    r'\.create\(|\.update\(|\.destroy\(|\.remove\()\b',
    re.IGNORECASE,
)

# Patterns that suggest the handler is only reading
READ_SIGNALS = re.compile(
    r'\b(select|find|get|fetch|query|filter|all\(\)|first\(\)|\.get\(|'
    r'\.list\(|\.retrieve\(|\.read\()\b',
    re.IGNORECASE,
)

# Regex to capture route+handler pairs from popular frameworks
ROUTE_PATTERNS: Dict[str, re.Pattern] = {
    'flask':   re.compile(
        r'@(?:\w+\.)?route\(["\']([^"\']+)["\'],\s*methods=\[([^\]]+)\]',
        re.DOTALL,
    ),
    'fastapi': re.compile(
        r'@(?:\w+\.)?(get|post|put|delete|patch|head|options)\(["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    'express': re.compile(
        r'(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
}

# Verb → expected semantic
METHOD_SEMANTICS: Dict[str, Dict] = {
    'GET':    {'should_mutate': False, 'weight': 1.0},
    'DELETE': {'should_mutate': True,  'weight': 0.8},
    'POST':   {'should_mutate': True,  'weight': 0.6},  # POST is broad — lower confidence
    'PUT':    {'should_mutate': True,  'weight': 1.0},
    'PATCH':  {'should_mutate': True,  'weight': 1.0},
}


def _extract_method_handler_pairs(source_code: str) -> List[Tuple[str, str]]:
    """Returns list of (HTTP_METHOD, handler_body_snippet) tuples."""
    pairs: List[Tuple[str, str]] = []

    # FastAPI / Express style: decorator immediately precedes function
    for framework, pattern in ROUTE_PATTERNS.items():
        for match in pattern.finditer(source_code):
            if framework == 'flask':
                methods_raw = match.group(2)
                methods = [m.strip().strip('"\'').upper() for m in methods_raw.split(',')]
                # Grab the next ~300 chars as proxy for handler body
                body_start = match.end()
                body_snippet = source_code[body_start:body_start + 400]
            else:
                methods = [match.group(1).upper()]
                body_start = match.end()
                body_snippet = source_code[body_start:body_start + 400]

            for method in methods:
                pairs.append((method, body_snippet))

    return pairs


def _score_pair(method: str, body: str) -> float:
    semantics = METHOD_SEMANTICS.get(method)
    if semantics is None:
        return 1.0  # Unknown method — don't penalise

    has_mutation = bool(MUTATION_SIGNALS.search(body))
    has_read     = bool(READ_SIGNALS.search(body))
    should_mutate = semantics['should_mutate']
    weight        = semantics['weight']

    if method == 'GET':
        if has_mutation and not has_read:
            return max(0.0, 1.0 - weight)   # Strong violation
        if has_mutation:
            return 0.5                        # Ambiguous — read + write
        return 1.0

    if method in ('PUT', 'PATCH', 'POST', 'DELETE'):
        if has_mutation:
            return 1.0
        if has_read and not has_mutation:
            return 0.6   # Probably fine (e.g. POST returning created resource)
        return 0.8       # No clear signals

    return 1.0


class HttpMethodCorrectness(Tool):
    def __init__(self):
        super().__init__(
            name="http_method_correctness",
            description=(
                "Scores whether HTTP methods (GET, POST, PUT, PATCH, DELETE) are used "
                "semantically correctly in REST API handlers, detecting common misuse patterns."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        pairs = _extract_method_handler_pairs(source_code)

        if not pairs:
            return 0.5  # No route definitions detected

        scores = [_score_pair(method, body) for method, body in pairs]
        return round(sum(scores) / len(scores), 4)