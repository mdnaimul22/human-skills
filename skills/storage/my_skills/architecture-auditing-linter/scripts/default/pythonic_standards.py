import ast
import re
from default.base import BaseRule, FileContext


class PythonicStandardsRule(BaseRule):
    CLASS_PATTERN = re.compile(r"^_?[A-Z][a-zA-Z0-9]*(?:_[A-Z][a-zA-Z0-9]*)?$")
    CONSECUTIVE_UPPER = re.compile(r"[A-Z]{4,}")
    SNAKE_CASE = re.compile(r"^[a-z_][a-z0-9_]*$")
    UPPER_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
    MAX_CLASS_LEN = 20
    MAX_CLASS_UNDERSCORES = 1
    MAX_CLASS_CONSECUTIVE_UPPER = 3
    MAX_FUNC_LEN = 25
    MAX_FUNC_UNDERSCORES = 3
    CRITICAL_BUILTINS = {
        "id", "type", "list", "dict", "str", "int", "float", "bool",
        "set", "tuple", "len", "range", "input", "format", "open",
        "map", "filter", "all", "any", "sum", "max", "min", "dir", "bytes"
    }

    def __init__(self, context: FileContext):
        super().__init__(context)
        self._class_depth = 0

    def _is_property(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for d in node.decorator_list:
            if isinstance(d, ast.Name) and d.id == "property":
                return True
            if isinstance(d, ast.Attribute) and d.attr == "property":
                return True
        return False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        core = node.name.lstrip("_")
        internal_underscores = core.count("_")

        if internal_underscores > self.MAX_CLASS_UNDERSCORES:
            self.add_violation(
                node,
                f"⚠️ [Naming Warning] Class '{node.name}' uses {internal_underscores} underscores (max allowed: {self.MAX_CLASS_UNDERSCORES}).",
                suggestion="Use PascalCase ('LightHouse') or at most one underscore ('Light_House')."
            )
        elif not self.CLASS_PATTERN.match(node.name):
            prefix = "_" if node.name.startswith("_") else ""
            suggested = f"{prefix}{core.capitalize()}"
            self.add_violation(
                node,
                f"❌ [PEP 8 Violation] Class '{node.name}' should follow PascalCase naming convention.",
                suggestion=f"Rename '{node.name}' to PascalCase (e.g. '{suggested}', 'LightHouse', or 'Light_House')."
            )

        upper_match = self.CONSECUTIVE_UPPER.search(core)
        if upper_match:
            self.add_violation(
                node,
                f"⚠️ [Naming Warning] Class '{node.name}' has more than {self.MAX_CLASS_CONSECUTIVE_UPPER} consecutive uppercase letters ('{upper_match.group(0)}').",
                suggestion="Use CamelCase for acronyms (e.g. 'GovernanceMcpGateway' instead of 'GovernanceMCPGateway')."
            )

        if len(core) > self.MAX_CLASS_LEN:
            self.add_violation(
                node,
                f"⚠️ [Naming Warning] Class '{node.name}' exceeds {self.MAX_CLASS_LEN}-character limit ({len(core)} chars).",
                suggestion=f"Shorten class name to <= {self.MAX_CLASS_LEN} characters."
            )

        if node.name in self.CRITICAL_BUILTINS:
            self.add_violation(
                node,
                f"❌ [Naming Violation] Class name '{node.name}' shadows a Python built-in.",
                suggestion="Rename the class to avoid shadowing core Python built-ins."
            )

        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def _check_func_name(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if node.name.startswith("__") and node.name.endswith("__"):
            return

        if self._is_property(node) and self.UPPER_CASE.match(node.name):
            return

        if not self.SNAKE_CASE.match(node.name):
            self.add_violation(
                node,
                f"❌ [PEP 8 Violation] Function '{node.name}' should follow snake_case naming convention (no uppercase letters).",
                suggestion=f"Rename '{node.name}' using lowercase snake_case (e.g. '{node.name.lower()}')."
            )

        core = node.name.lstrip("_")
        internal_underscores = core.count("_")
        if internal_underscores > self.MAX_FUNC_UNDERSCORES:
            self.add_violation(
                node,
                f"⚠️ [Naming Warning] Function '{node.name}' uses {internal_underscores} underscores (max allowed: {self.MAX_FUNC_UNDERSCORES}).",
                suggestion=f"Use a more concise snake_case name with at most {self.MAX_FUNC_UNDERSCORES} underscores."
            )

        if len(core) > self.MAX_FUNC_LEN:
            self.add_violation(
                node,
                f"⚠️ [Naming Warning] Function '{node.name}' exceeds {self.MAX_FUNC_LEN}-character limit ({len(core)} chars).",
                suggestion=f"Shorten function name to <= {self.MAX_FUNC_LEN} characters."
            )

        if self._class_depth == 0 and node.name in self.CRITICAL_BUILTINS:
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
