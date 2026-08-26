import ast
import re
from typing import Any
from helpers.tool import Tool


# ── Response contract patterns ────────────────────────────────────────────────

# Pydantic / dataclass / TypedDict — structured response models
RESPONSE_MODEL_PATTERNS = re.compile(
    r'\b(BaseModel|BaseSchema|Schema|TypedDict|dataclass|'
    r'response_model\s*=|ResponseModel|Serializer|serializers\.ModelSerializer)\b'
)

# Raw dict returns — unstable contract
RAW_DICT_RETURN = re.compile(
    r'return\s+\{[^}]*\}|'
    r'return\s+jsonify\s*\(\s*\{|'
    r'return\s+JSONResponse\s*\(\s*content\s*=\s*\{|'
    r'return\s+JsonResponse\s*\(\s*\{'
)

# Optional field markers
OPTIONAL_FIELD = re.compile(
    r'\bOptional\[|'
    r'\|\s*None\b|'
    r':\s*\w+\s*=\s*None\b|'
    r'Field\s*\([^)]*default\s*=\s*None'
)

# Required field without default (breaking if added to existing model)
# Only match class-body field annotations like `name: str` that lack `= ...`
REQUIRED_NO_DEFAULT = re.compile(
    r'^\s{4}\w+:\s*(?:str|int|float|bool|list|dict|List|Dict|Set)\s*$',
    re.MULTILINE,
)

# Deprecation signals
DEPRECATION_MARKERS = re.compile(
    r'@deprecated|'
    r'deprecated\s*=\s*True|'
    r'Deprecated|'
    r'DEPRECATED|'
    r'DeprecationWarning|'
    r'warnings\.warn\s*\([^)]*deprecat|'
    r'X-Deprecated|'
    r'["\']Sunset["\']|'
    r'["\']Deprecation["\']|'
    r'sunset',
    re.IGNORECASE,
)

# Consistent error response patterns
ERROR_SCHEMA_PATTERNS = re.compile(
    r'HTTPException\s*\(\s*status_code\s*=.*?detail\s*=|'
    r'raise\s+HTTPException|'
    r'abort\s*\(\s*\d{3}|'
    r'return\s+Response\s*\([^)]*status\s*=\s*[45]\d{2}|'
    r'JsonResponse\s*\([^)]*status\s*=\s*[45]\d{2}',
    re.DOTALL,
)

# Structured error detail (dict with message/code keys)
STRUCTURED_ERROR = re.compile(
    r'detail\s*=\s*\{[^}]*(message|error|code)[^}]*\}|'
    r'\"error\"\s*:|'
    r'\"message\"\s*:|'
    r'\"detail\"\s*:'
)

# Status code override / inconsistency signals
STATUS_OVERRIDE_PATTERNS = re.compile(
    r'status_code\s*=\s*(?:status\.)?HTTP_\d+|'
    r'status_code\s*=\s*\d{3}|'
    r'\.status_code\s*=\s*\d{3}'
)

# Mixed response types — returning both dict and model in same handler
MIXED_RESPONSE = re.compile(
    r'(return\s+\{[^}]*\}.*?return\s+\w+Model|'
    r'return\s+\w+Model.*?return\s+\{[^}]*\})',
    re.DOTALL,
)


class BreakingChangeRisk(Tool):
    def __init__(self):
        super().__init__(
            name="breaking_change_risk",
            description=(
                "Scores API code for breaking change risk: checks response model "
                "stability, Optional field usage, deprecation markers, error "
                "consistency, and contract safety patterns."
            ),
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        score = 0.0
        suggestions = []

        # 1. Response model usage (0.20) — structured models = stable contracts
        if RESPONSE_MODEL_PATTERNS.search(source_code):
            score += 0.20
        else:
            raw_count = len(RAW_DICT_RETURN.findall(source_code))
            if raw_count > 0:
                suggestions.append(
                    "Use Pydantic models or dataclasses for API responses "
                    "instead of raw dicts. Structured models create stable "
                    "contracts and make breaking changes visible."
                )

        # 2. Optional field usage (0.20) — safe field evolution
        optional_count = len(OPTIONAL_FIELD.findall(source_code))
        if optional_count >= 3:
            score += 0.20
        elif optional_count >= 1:
            score += 0.10
            suggestions.append(
                "Mark non-essential response fields as Optional[T] to allow "
                "safe field removal without breaking clients."
            )
        else:
            suggestions.append(
                "No Optional fields detected. Use Optional[T] or default "
                "values for fields that may be removed in the future."
            )

        # 3. Default values on fields (0.15) — safe field addition
        default_count = len(re.findall(
            r'Field\s*\([^)]*default\s*=|'
            r':\s*\w+\s*=\s*(?:None|""|\[\]|\{\}|0|False|True)',
            source_code,
        ))
        required_count = len(REQUIRED_NO_DEFAULT.findall(source_code))
        if default_count > 0 and required_count == 0:
            score += 0.15
        elif default_count > required_count:
            score += 0.08
            suggestions.append(
                f"Found {required_count} required field(s) without defaults. "
                "Adding required fields to existing models breaks clients. "
                "Use default values for backward compatibility."
            )
        elif required_count > 0:
            suggestions.append(
                f"RISK: {required_count} required field(s) without default "
                "values detected. New required fields break existing clients. "
                "Always provide defaults or make fields Optional."
            )

        # 4. Deprecation markers (0.15) — signals proper lifecycle management
        if DEPRECATION_MARKERS.search(source_code):
            score += 0.15
        # Only suggest if there's substantial code (not a tiny snippet)
        elif len(source_code) > 500:
            suggestions.append(
                "No deprecation markers found. Use @deprecated decorators "
                "or Sunset/Deprecation headers to signal upcoming changes."
            )

        # 5. Consistent error schema (0.15) — predictable error responses
        error_count = len(ERROR_SCHEMA_PATTERNS.findall(source_code))
        if error_count > 0:
            if STRUCTURED_ERROR.search(source_code):
                score += 0.15
            else:
                score += 0.08
                suggestions.append(
                    "Use structured error responses with consistent fields "
                    "(e.g., {\"detail\": {\"message\": ..., \"code\": ...}}) "
                    "instead of plain strings."
                )

        # 6. Status code consistency (0.15) — no unexpected changes
        status_matches = STATUS_OVERRIDE_PATTERNS.findall(source_code)
        if len(status_matches) <= 1:
            score += 0.15
        elif len(set(status_matches)) <= 3:
            score += 0.10
        else:
            suggestions.append(
                "Multiple different status code overrides detected. "
                "Standardize responses to avoid breaking client expectations."
            )

        # ── Penalties ─────────────────────────────────────────────────────────

        # P1: Raw dict returns alongside models = unstable contract
        has_model = bool(RESPONSE_MODEL_PATTERNS.search(source_code))
        has_raw = bool(RAW_DICT_RETURN.search(source_code))
        if has_model and has_raw:
            score -= 0.15
            suggestions.append(
                "RISK: Mixing raw dict returns with response models in the "
                "same module. Standardize on models for contract stability."
            )

        # P2: AST-based: function returns different types
        if module is not None:
            mixed = self._check_mixed_returns(module)
            if mixed:
                score -= 0.10
                suggestions.append(
                    "RISK: Some handlers return inconsistent types across "
                    "branches. Ensure all return paths use the same model."
                )

        return round(min(max(score, 0.0), 1.0), 4), suggestions

    @staticmethod
    def _check_mixed_returns(module: ast.Module) -> bool:
        """Check if any function has return statements with mixed types."""
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return) and n.value]
                if len(returns) < 2:
                    continue
                types = set()
                for ret in returns:
                    if isinstance(ret.value, ast.Dict):
                        types.add("dict")
                    elif isinstance(ret.value, ast.Call):
                        types.add("call")
                    elif isinstance(ret.value, ast.Constant):
                        types.add("const")
                if len(types) > 1 and "dict" in types:
                    return True
        return False
