import ast
import re
from typing import Any, List
from helpers.tool import Tool

SPECIFIC_EXCEPTIONS = re.compile(
    r'except\s+(ValueError|TypeError|KeyError|IndexError|AttributeError|'
    r'RuntimeError|OSError|IOError|FileNotFoundError|PermissionError|'
    r'NotFoundError|ValidationError|IntegrityError|OperationalError|'
    r'ConnectionError|TimeoutError|HTTPException|RequestException|'
    r'InsufficientFundsError|SQLAlchemyError|DatabaseError)\b',
    re.IGNORECASE,
)

GLOBAL_ERROR_HANDLERS = re.compile(
    r'(@app\.errorhandler|@app\.exception_handler|'
    r'exception_handler\s*\(|add_exception_handler|'
    r'EXCEPTION_HANDLER|middleware.*error|ErrorMiddleware|'
    r'HTTPException.*handler|def\s+handle_.*error)\b',
    re.IGNORECASE,
)

JSON_ERROR_RESPONSE = re.compile(
    r'(jsonify|JSONResponse|Response)\s*\(\s*\{|'
    r'\{"error"|\{"message"|\{"detail"|\{"status"|\{"debug"|"status_code"|'
    r'content=\{"detail"',
    re.IGNORECASE,
)

ERROR_LOGGING = re.compile(
    r'\b(logger\.(error|exception|critical|warning|info)|'
    r'logging\.(error|exception|critical|warning|info)|'
    r'log\.(error|exception|critical|warning|info)|sentry|rollbar|bugsnag|'
    r'capture_exception|capture_message)\b',
    re.IGNORECASE,
)

TRACEBACK_LEAK = re.compile(
    r'traceback\.format_exc|str\(e\)|repr\(e\)|traceback\.print_exc',
    re.IGNORECASE,
)

DB_FAILURE_HANDLING = re.compile(
    r'\b(OperationalError|IntegrityError|DatabaseError|'
    r'SQLAlchemyError|session\.rollback|db\.session\.rollback|'
    r'transaction.*rollback|rollback\(\)|transaction\.atomic)\b',
    re.IGNORECASE,
)


class _ExceptionQualityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.bare_count     = 0
        self.broad_count    = 0
        self.specific_count = 0
        self.swallowed      = 0

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.bare_count += 1
            body = node.body
            if len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Expr)) and \
               (isinstance(body[0], ast.Pass) or (isinstance(body[0].value, ast.Constant) and body[0].value.value is Ellipsis)):
                self.swallowed += 1
        elif isinstance(node.type, ast.Name) and node.type.id in ('Exception', 'BaseException'):
            self.broad_count += 1
            body = node.body
            if len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Expr)) and \
               (isinstance(body[0], ast.Pass) or (isinstance(body[0].value, ast.Constant) and body[0].value.value is Ellipsis)):
                self.swallowed += 1
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
        
        clean_code = re.sub(r'#.*', '', source_code)
        
        exc_stats = _analyse_exceptions(source_code)
        
        if exc_stats:
            total = exc_stats.bare_count + exc_stats.broad_count + exc_stats.specific_count
            if total > 0:
                specificity_ratio = exc_stats.specific_count / total
                score += specificity_ratio * 0.20
                score -= exc_stats.bare_count * 0.10
                score -= exc_stats.swallowed * 0.12
            else:
                score -= 0.10
        else:
            score -= 0.10

        if GLOBAL_ERROR_HANDLERS.search(clean_code):
            score += 0.20

        if JSON_ERROR_RESPONSE.search(clean_code):
            score += 0.15

        if ERROR_LOGGING.search(clean_code):
            score += 0.20

        if TRACEBACK_LEAK.search(clean_code):
            score -= 0.50
        else:
            score += 0.10
            
        if DB_FAILURE_HANDLING.search(clean_code):
            score += 0.15

        return round(min(max(score, 0.0), 1.0), 4)