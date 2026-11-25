import ast
from default.base import BaseRule, FileContext


class ManualIORule(BaseRule):
    def __init__(self, context: FileContext):
        super().__init__(context)
        self._with_open_ids: set[int] = set()
        self._open_shadowed = False

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        if self.ctx.is_config_file:
            return [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "builtins":
                if any((a.asname or a.name) == "open" for a in node.names):
                    self._open_shadowed = True
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "open":
                self._open_shadowed = True
        return super().run(tree)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if not self._open_shadowed and id(node) not in self._with_open_ids:
                self.add_violation(node, "❌ [Manual File I/O] Direct 'open()' call found. Use 'read_text/write_text' from config instead.")

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr in ("open", "read", "write"):
                self.add_violation(node, f"❌ [Manual File I/O] Direct 'os.{node.func.attr}()' used. Use config utilities.")

        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        if not self._open_shadowed:
            for item in node.items:
                if isinstance(item.context_expr, ast.Call):
                    call = item.context_expr
                    if isinstance(call.func, ast.Name) and call.func.id == "open":
                        self._with_open_ids.add(id(call))
                        self.add_violation(node, "❌ [Manual File I/O] 'with open()' block found. Use 'read_text/write_text' from config instead.")
        self.generic_visit(node)
