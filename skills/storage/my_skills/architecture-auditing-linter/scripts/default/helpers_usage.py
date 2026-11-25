import ast
from default.base import BaseRule, FileContext


class HelpersUsageRule(BaseRule):
    def __init__(self, context: FileContext):
        super().__init__(context)
        self._loop_depth = 0
        self._except_depth = 0

    def visit_For(self, node: ast.For) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._except_depth += 1
        self.generic_visit(node)
        self._except_depth -= 1

    def visit_Call(self, node: ast.Call) -> None:
        if not self.ctx.is_helpers_file and not self.ctx.is_config_file:
            if isinstance(node.func, ast.Attribute) and node.func.attr in ("now", "utcnow"):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "datetime":
                    self.add_violation(
                        node,
                        "⚠️ [Helpers Violation] Direct 'datetime.now()/utcnow()' used. Use 'get_now_utc()' or 'get_now_iso()' from src.helpers instead."
                    )

            if isinstance(node.func, ast.Name) and node.func.id == "create_async_engine" and not self.ctx.is_db_file:
                self.add_violation(node, "❌ [Helpers Violation] Direct 'create_async_engine()' used. Use 'init_db()' from src.db instead.")

            if self._loop_depth > 0 and self._except_depth > 0 and isinstance(node.func, ast.Attribute) and node.func.attr == "sleep":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "time":
                    self.add_violation(node, "⚠️ [Helpers Violation] Manual retry pattern detected (time.sleep in loop). Use '@retry_on_failure' from src.helpers instead.")
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "asyncio":
                    self.add_violation(node, "⚠️ [Helpers Violation] Manual async retry pattern detected (asyncio.sleep in loop). Use '@retry_async_on_failure' from src.helpers instead.")

        self.generic_visit(node)
