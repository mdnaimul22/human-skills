import ast
import re
from typing import Any, List
from helpers.tool import Tool

BARE_EXCEPT = re.compile(r'except\s*:', re.MULTILINE)
EXCEPT_EXCEPTION = re.compile(r'except\s+Exception\s*:', re.MULTILINE)
BROAD_CATCHES = re.compile(r'except\s+(Exception|BaseException)\s*(as\s+\w+)?\s*:', re.MULTILINE)

SPECIFIC_EXCEPTIONS = re.compile(
    r'except\s+(ValueError|TypeError|KeyError|IndexError|AttributeError|'
    r'RuntimeError|OSError|IOError|FileNotFoundError|PermissionError|'
    r'NotFoundError|ValidationError|IntegrityError|OperationalError|'
    r'ConnectionError|TimeoutError|HTTPException|RequestException)\s*',
    re.IGNORECASE,
)

GLOBAL_ERROR_HANDLERS = re.compile(
    r'(@app\.errorhandler|@app\.exception_handler|'
    r'exception_handler\s*\(|add_exception_handler|'
    r'EXCEPTION_HANDLER|middleware.*error|ErrorMiddleware|'
    r'HTTPException.*handler)\b',
    re.IGNORECASE,
)

JSON_ERROR_RESPONSE = re.compile(
    r'\b(jsonify\s*\(\s*\{|JSONResponse\s*\(\s*\{|'
    r'{"error"|{"message"|{"detail"|"status_code")\b',
    re.IGNORECASE,
)

ERROR_LOGGING = re.compile(
    r'\b(logger\.(error|exception|critical|warning)|'
    r'logging\.(error|exception|critical|warning)|'
    r'log\.error|log\.exception|sentry|rollbar|bugsnag|'
    r'capture_exception|capture_message)\b',
    re.IGNORECASE,
)

TRACEBACK_LEAK = re.compile(
    r'\b(traceback\.print_exc|traceback\.format_exc.*return|'
    r'str\(e\).*return|repr\(e\).*return)\b',
    re.IGNORECASE,
)

SILENT_SWALLOW = re.compile(
    r'except[^:]*:\s*\n\s*(pass\s*$|\.\.\.)',
    re.MULTILINE,
)

DB_FAILURE_HANDLING = re.compile(
    r'\b(OperationalError|IntegrityError|DatabaseError|'
    r'SQLAlchemyError|session\.rollback|db\.session\.rollback|'
    r'transaction.*rollback|rollback\(\))\b',
    re.IGNORECASE,
)


class _ExceptionQualityVisitor(ast.NodeVisitor):
    """Counts bare, broad, and specific exception handlers."""

    def __init__(self):
        self.bare_count     = 0
        self.broad_count    = 0
        self.specific_count = 0
        self.swallowed      = 0   # except: pass

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.bare_count += 1
            body = node.body
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                self.swallowed += 1
        elif isinstance(node.type, ast.Name) and node.type.id in ('Exception', 'BaseException'):
            self.broad_count += 1
        else:
            self.specific_count += 1
        self.generic_visit(node)


def _analyse_exceptions(source_code: str):
    try:
        tree = ast.parse(source_code)
        visitor = _ExceptionQualityVisitor()
        visitor.visit(tree)
        return visitor
    except SyntaxError:
        return None


class ErrorHandling(Tool):
    def __init__(self):
        super().__init__(
            name="error_handling",
            description=(
                "Scores error handling quality in REST API code: checks for specific exception "
                "types, global error handlers, consistent JSON error responses, error logging, "
                "absence of traceback leaks, and DB failure handling."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        score = 0.0

        # AST analysis
        exc_stats = _analyse_exceptions(source_code)

        if exc_stats:
            total = exc_stats.bare_count + exc_stats.broad_count + exc_stats.specific_count
            if total > 0:
                # 1. Reward specific exception handling (0.20)
                specificity_ratio = exc_stats.specific_count / total
                score += specificity_ratio * 0.20

                # Penalise bare except
                score -= exc_stats.bare_count * 0.10

                # Penalise silently swallowed exceptions
                score -= exc_stats.swallowed * 0.12
            else:
                # No exception handling at all in parseable code
                score -= 0.10

        # 2. Global / centralised error handlers (0.20)
        if GLOBAL_ERROR_HANDLERS.search(source_code):
            score += 0.20

        # 3. Consistent JSON error response structure (0.15)
        if JSON_ERROR_RESPONSE.search(source_code):
            score += 0.15

        # 4. Error logging (0.20)
        if ERROR_LOGGING.search(source_code):
            score += 0.20

        # 5. No traceback leak to clients (0.10)
        if not TRACEBACK_LEAK.search(source_code):
            score += 0.10
        else:
            score -= 0.15

        # 6. DB failure / rollback handling (0.15)
        if DB_FAILURE_HANDLING.search(source_code):
            score += 0.15

        return round(min(max(score, 0.0), 1.0), 4)