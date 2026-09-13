import ast
from default.base import BaseRule


class SilentExceptionsRule(BaseRule):
    RAW_EXCEPTION_TYPES = {"Exception", "ValueError", "RuntimeError", "TypeError", "KeyError"}

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                self.add_violation(handler, "❌ [Silent Exception] 'except: pass' found. Do not swallow exceptions silently.")
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if not self.ctx.is_helpers_file and not self.ctx.is_config_file and node.exc:
            exc_node = node.exc
            exc_name = None
            if isinstance(exc_node, ast.Call) and isinstance(exc_node.func, ast.Name):
                exc_name = exc_node.func.id
            elif isinstance(exc_node, ast.Name):
                exc_name = exc_node.id
            if exc_name and exc_name in self.RAW_EXCEPTION_TYPES:
                self.add_violation(
                    node,
                    f"⚠️ [Helpers Violation] Raw 'raise {exc_name}(...)' used. Use AppError subclasses (NotFoundError, ValidationError, etc.) from src.helpers instead."
                )
        self.generic_visit(node)
