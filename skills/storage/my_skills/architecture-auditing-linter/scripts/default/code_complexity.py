import ast
from default.base import BaseRule


class CodeComplexityRule(BaseRule):
    def __init__(self, context):
        super().__init__(context)
        self._current_depth = 0
        self._max_reported_depth: dict[int, int] = {}

    def _enter_block(self, node: ast.AST) -> None:
        self._current_depth += 1
        if self._current_depth > 4:
            if node.lineno not in self._max_reported_depth:
                self._max_reported_depth[node.lineno] = self._current_depth
                self.add_violation(
                    node,
                    f"⚠️ [Complexity Warning] Deep nesting depth of {self._current_depth} levels detected.",
                    suggestion="Flatten nested logic using guard clauses, early returns, or helper extraction."
                )

    def _exit_block(self) -> None:
        self._current_depth = max(0, self._current_depth - 1)

    def visit_If(self, node: ast.If) -> None:
        self._enter_block(node)
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            self._exit_block()
            self.visit(node.orelse[0])
            return
        for stmt in node.orelse:
            self.visit(stmt)
        self._exit_block()

    def visit_For(self, node: ast.For) -> None:
        self._enter_block(node)
        self.generic_visit(node)
        self._exit_block()

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._enter_block(node)
        self.generic_visit(node)
        self._exit_block()

    def visit_While(self, node: ast.While) -> None:
        self._enter_block(node)
        self.generic_visit(node)
        self._exit_block()

    def visit_Try(self, node: ast.Try) -> None:
        self._enter_block(node)
        self.generic_visit(node)
        self._exit_block()

    def _count_branches(self, node: ast.AST) -> int:
        count = 0
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp)):
                count += 1
            elif isinstance(child, ast.BoolOp):
                count += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                count += len(child.ifs)
            count += self._count_branches(child)
        return count

    def _check_function_complexity(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        branch_count = 1 + self._count_branches(node)

        if branch_count > 15:
            self.add_violation(
                node,
                f"⚠️ [Complexity Warning] Function '{node.name}' has high cyclomatic complexity ({branch_count}).",
                suggestion="Refactor complex branching into separate polymorphic strategies or smaller single-responsibility functions."
            )

        if len(node.body) > 60:
            self.add_violation(
                node,
                f"⚠️ [Complexity Warning] Function '{node.name}' is too long ({len(node.body)} statements).",
                suggestion="Decompose long function into focused, reusable helper functions."
            )

    def _visit_scoped_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._check_function_complexity(node)
        saved_depth = self._current_depth
        self._current_depth = 0
        self.generic_visit(node)
        self._current_depth = saved_depth

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_scoped_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_scoped_func(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        saved_depth = self._current_depth
        self._current_depth = 0
        self.generic_visit(node)
        self._current_depth = saved_depth
