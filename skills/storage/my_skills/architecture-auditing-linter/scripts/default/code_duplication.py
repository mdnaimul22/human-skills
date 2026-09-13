import ast
import copy
import hashlib
from collections import defaultdict
from default.base import BaseRule


class CodeDuplicationRule(BaseRule):
    def __init__(self, context):
        super().__init__(context)
        self._functions: list[tuple[str, int, ast.AST, list[ast.AST]]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if len(node.body) >= 3:
            self._functions.append((node.name, node.lineno, node, node.body))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if len(node.body) >= 3:
            self._functions.append((node.name, node.lineno, node, node.body))
        self.generic_visit(node)

    def _normalize_body(self, body_nodes: list[ast.AST]) -> str:
        parts = []
        for node in body_nodes:
            copied = copy.deepcopy(node)
            for child in ast.walk(copied):
                if isinstance(child, ast.Name):
                    child.id = "_"
                elif isinstance(child, ast.Constant):
                    child.value = 0
                elif isinstance(child, ast.Attribute):
                    child.attr = "_"
            parts.append(ast.dump(copied))
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def post_check(self) -> None:
        if len(self._functions) < 2:
            return

        hashes = defaultdict(list)
        for name, lineno, node, body in self._functions:
            body_hash = self._normalize_body(body)
            hashes[body_hash].append((name, lineno, node))

        for body_hash, matches in hashes.items():
            if len(matches) > 1:
                first_name, first_line, _ = matches[0]
                for name, lineno, node in matches[1:]:
                    self.add_violation(
                        node,
                        f"❌ [DRY Violation] Identical code structure detected with function '{first_name}' (L{first_line}).",
                        suggestion=f"Consolidate duplicated logic between '{name}' and '{first_name}' into a shared, reusable helper function."
                    )
