import ast
import re
from typing import Any, List, Set
from helpers.tool import Tool


# ORM / DB call signals
DB_CALL_PATTERNS = re.compile(
    r'\b(\.query\(|\.filter\(|\.get\(|\.find\(|\.findOne\(|\.findAll\(|'
    r'\.select\(|\.execute\(|\.fetch\(|\.fetchall\(|\.fetchone\(|'
    r'session\.query|db\.query|cursor\.execute|Model\.objects\.|'
    r'\.where\(|\.join\(|\.load\(|\.all\(\)|\.first\(\)|\.one\(\))\b',
    re.IGNORECASE,
)

# Eager-loading mitigation signals
EAGER_LOAD_PATTERNS = re.compile(
    r'\b(joinedload|subqueryload|selectinload|contains_eager|'
    r'select_related|prefetch_related|eager_load|includes|with_related)\b',
    re.IGNORECASE,
)

# Loop constructs in source text
LOOP_PATTERNS = re.compile(
    r'\b(for\s+\w|while\s+\w|\.map\(|\.forEach\(|list\(.*for\s)'
)


class _LoopQueryVisitor(ast.NodeVisitor):
    """AST visitor that counts DB calls found inside loops."""

    def __init__(self):
        self.violations: List[int] = []   # line numbers
        self._in_loop_depth = 0

    def _enter_loop(self, node):
        self._in_loop_depth += 1
        self.generic_visit(node)
        self._in_loop_depth -= 1

    visit_For      = _enter_loop
    visit_While    = _enter_loop
    visit_ListComp = _enter_loop
    visit_SetComp  = _enter_loop
    visit_DictComp = _enter_loop
    visit_GeneratorExp = _enter_loop

    def visit_Call(self, node: ast.Call):
        if self._in_loop_depth > 0:
            # Check if the call looks like a DB call
            call_str = ast.unparse(node)
            if DB_CALL_PATTERNS.search(call_str):
                self.violations.append(node.lineno)
        self.generic_visit(node)


def _count_ast_violations(source_code: str) -> int:
    try:
        tree = ast.parse(source_code)
        visitor = _LoopQueryVisitor()
        visitor.visit(tree)
        return len(visitor.violations)
    except SyntaxError:
        return 0


def _count_regex_violations(source_code: str) -> int:
    """Fallback regex-based heuristic for non-Python or unparseable code."""
    violations = 0
    lines = source_code.split('\n')
    in_loop = False
    loop_indent = 0

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Detect loop start
        if re.match(r'(for |while )', stripped):
            in_loop = True
            loop_indent = indent
        elif in_loop and indent <= loop_indent and stripped and not stripped.startswith('#'):
            in_loop = False

        if in_loop and DB_CALL_PATTERNS.search(line):
            violations += 1

    return violations


def _has_eager_loading(source_code: str) -> bool:
    return bool(EAGER_LOAD_PATTERNS.search(source_code))


class N1QueryDetector(Tool):
    def __init__(self):
        super().__init__(
            name="n1_query_detection",
            description=(
                "Detects N+1 query anti-patterns in API code: database calls inside loops "
                "without eager-loading. Higher score means fewer N+1 risks."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        # Try AST-based detection first; fall back to regex
        ast_violations = _count_ast_violations(source_code)
        regex_violations = _count_regex_violations(source_code)

        # Take the max (conservative — rather over-report than miss)
        violations = max(ast_violations, regex_violations)

        has_mitigation = _has_eager_loading(source_code)
        suggestions = []

        if violations == 0:
            return 1.0, []

        # Each violation degrades score; mitigation halves the penalty
        penalty_per_violation = 0.25 if not has_mitigation else 0.12
        penalty = min(violations * penalty_per_violation, 1.0)
        
        suggestions.append(f"Detected {violations} potential N+1 query loop(s). Move database calls outside loops or use JOINs/bulk fetch.")
        if not has_mitigation:
            suggestions.append("Use eager loading (e.g. select_related, joinedload, prefetch_related) to load related database objects efficiently.")

        return round(max(0.0, 1.0 - penalty), 4), suggestions