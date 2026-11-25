import ast
from default.base import BaseRule, FileContext


class SilentExceptionsRule(BaseRule):
    RAW_EXCEPTION_TYPES = {"Exception", "ValueError", "RuntimeError", "TypeError", "KeyError"}
    BROAD_EXCEPTIONS = {"Exception", "BaseException"}
    VALIDATOR_DECORATORS = {"field_validator", "model_validator", "validator", "root_validator"}

    def __init__(self, context: FileContext):
        super().__init__(context)
        self._exempt_raise_depth = 0

    def _is_broad_handler(self, handler: ast.ExceptHandler) -> bool:
        if handler.type is None:
            return True
        if isinstance(handler.type, ast.Name) and handler.type.id in self.BROAD_EXCEPTIONS:
            return True
        if isinstance(handler.type, ast.Tuple):
            return any(isinstance(e, ast.Name) and e.id in self.BROAD_EXCEPTIONS for e in handler.type.elts)
        return False

    def _is_exempt_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        if node.name.startswith("__") and node.name.endswith("__"):
            return True
        for dec in node.decorator_list:
            dec_name = None
            if isinstance(dec, ast.Name):
                dec_name = dec.id
            elif isinstance(dec, ast.Attribute):
                dec_name = dec.attr
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    dec_name = dec.func.id
                elif isinstance(dec.func, ast.Attribute):
                    dec_name = dec.func.attr
            if dec_name in self.VALIDATOR_DECORATORS:
                return True
        return False

    def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        exempt = self._is_exempt_func(node)
        if exempt:
            self._exempt_raise_depth += 1
        self.generic_visit(node)
        if exempt:
            self._exempt_raise_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func(node)

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                if self._is_broad_handler(handler):
                    self.add_violation(handler, "❌ [Silent Exception] 'except: pass' found. Do not swallow exceptions silently.")
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if not self.ctx.is_helpers_file and not self.ctx.is_config_file and self._exempt_raise_depth == 0 and node.exc:
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
