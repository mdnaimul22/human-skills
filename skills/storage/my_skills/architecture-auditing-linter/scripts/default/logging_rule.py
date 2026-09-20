import ast
from default.base import BaseRule


class LoggingRule(BaseRule):
    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        if self.ctx.is_test_file:
            return [], []
        return super().run(tree)

    def visit_Import(self, node: ast.Import) -> None:
        if self.ctx.is_test_file:
            return
        for alias in node.names:
            if alias.name == "logging" or alias.name.startswith("logging."):
                self.add_violation(node, "❌ [Logging Violation] Direct 'import logging' used. Use 'setup_logger' instead.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self.ctx.is_test_file:
            return
        if node.module == "logging" or (node.module and node.module.startswith("logging.")):
            self.add_violation(node, "❌ [Logging Violation] Direct 'logging' import used. Use 'setup_logger' instead.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self.ctx.is_test_file:
            return
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.add_violation(node, "⚠️ [Print Statement] Manual 'print()' found. Use a logger for production code.")

        if isinstance(node.func, ast.Name) and node.func.id == "setup_logger":
            if node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    self.add_violation(node, f"❌ [Logger Compliance] Hardcoded log filename '{arg.value}' found. Use 'Settings.LOG_DIR / \"layer.log\"'.")

        self.generic_visit(node)
