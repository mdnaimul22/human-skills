import ast
import re
from default.base import BaseRule


class PythonicStandardsRule(BaseRule):
    PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
    SNAKE_CASE = re.compile(r"^[a-z_][a-z0-9_]*$")
    UPPER_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
    CRITICAL_BUILTINS = {
        "id", "type", "list", "dict", "str", "int", "float", "bool",
        "set", "tuple", "len", "range", "input", "format", "open",
        "map", "filter", "all", "any", "sum", "max", "min", "dir", "bytes"
    }

    def _is_property(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for d in node.decorator_list:
            if isinstance(d, ast.Name) and d.id == "property":
                return True
            if isinstance(d, ast.Attribute) and d.attr == "property":
                return True
        return False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not self.PASCAL_CASE.match(node.name):
            self.add_violation(
                node,
                f"❌ [PEP 8 Violation] Class '{node.name}' should follow PascalCase naming convention.",
                suggestion=f"Rename '{node.name}' to PascalCase (e.g. '{node.name.capitalize()}')."
            )

        if node.name in self.CRITICAL_BUILTINS:
            self.add_violation(
                node,
                f"❌ [Naming Violation] Class name '{node.name}' shadows a Python built-in.",
                suggestion="Rename the class to avoid shadowing core Python built-ins."
            )

        self.generic_visit(node)

    def _check_func_name(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if node.name.startswith("__") and node.name.endswith("__"):
            return

        if self._is_property(node) and self.UPPER_CASE.match(node.name):
            return

        if not self.SNAKE_CASE.match(node.name):
            self.add_violation(
                node,
                f"❌ [PEP 8 Violation] Function '{node.name}' should follow snake_case naming convention.",
                suggestion=f"Rename '{node.name}' using snake_case with lowercase letters and underscores."
            )

        if node.name in self.CRITICAL_BUILTINS:
            self.add_violation(
                node,
                f"❌ [Naming Violation] Function name '{node.name}' shadows a Python built-in.",
                suggestion="Rename the function to avoid shadowing core Python built-ins."
            )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_func_name(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_func_name(node)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        names = ", ".join(node.names)
        self.add_violation(
            node,
            f"❌ [Architecture Violation] 'global {names}' statement used.",
            suggestion="Avoid global state mutation. Refactor using dependency injection, explicit method parameters, or encapsulate state within a class instance."
        )
        self.generic_visit(node)
