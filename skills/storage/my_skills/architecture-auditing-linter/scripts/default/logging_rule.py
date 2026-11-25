import ast
from default.base import BaseRule, FileContext


class LoggingRule(BaseRule):
    TYPE_ONLY_LOGGING_IMPORTS = {"Logger", "LoggerAdapter", "LogRecord"}

    def __init__(self, context: FileContext):
        super().__init__(context)
        self._in_type_checking = 0

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        if self.ctx.is_test_file:
            return [], []
        return super().run(tree)

    @staticmethod
    def _is_type_checking_guard(test: ast.expr) -> bool:
        if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
            return True
        if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
            return True
        return False

    def visit_If(self, node: ast.If) -> None:
        if self._is_type_checking_guard(node.test):
            self._in_type_checking += 1
            for stmt in node.body:
                self.visit(stmt)
            self._in_type_checking -= 1
            for stmt in node.orelse:
                self.visit(stmt)
            return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        if self.ctx.is_test_file or self._in_type_checking > 0:
            return
        for alias in node.names:
            if alias.name == "logging" or alias.name.startswith("logging."):
                self.add_violation(node, "❌ [Logging Violation] Direct 'import logging' used. Use 'setup_logger' instead.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self.ctx.is_test_file or self._in_type_checking > 0:
            return
        if node.module == "logging" or (node.module and node.module.startswith("logging.")):
            imported = {a.name for a in node.names}
            if imported and imported.issubset(self.TYPE_ONLY_LOGGING_IMPORTS):
                self.generic_visit(node)
                return
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
