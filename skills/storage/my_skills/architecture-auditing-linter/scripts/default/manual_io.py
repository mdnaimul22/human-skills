import ast
from default.base import BaseRule


class ManualIORule(BaseRule):
    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            self.add_violation(node, "❌ [Manual File I/O] Direct 'open()' call found. Use 'read_text/write_text' from config instead.")

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr in ("open", "read", "write"):
                self.add_violation(node, f"❌ [Manual File I/O] Direct 'os.{node.func.attr}()' used. Use config utilities.")

        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                call = item.context_expr
                if isinstance(call.func, ast.Name) and call.func.id == "open":
                    self.add_violation(node, "❌ [Manual File I/O] 'with open()' block found. Use 'read_text/write_text' from config instead.")
        self.generic_visit(node)
