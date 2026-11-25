import ast
from default.base import BaseRule, FileContext


class FutureAnnotationsRule(BaseRule):
    def __init__(self, context: FileContext):
        super().__init__(context)
        self._has_future_annotations = False
        self._type_checking_names: set[str] = set()

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        if not isinstance(tree, ast.Module):
            return [], []

        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                if any(a.name == "annotations" for a in node.names):
                    self._has_future_annotations = True
                    return [], []

        self._collect_type_checking_names(tree)
        self._check_type_checking_usage(tree)
        self._check_class_self_references(tree)
        return self.violations, self.advisories

    @staticmethod
    def _is_type_checking_guard(test: ast.expr) -> bool:
        if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
            return True
        if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
            return True
        return False

    def _collect_type_checking_names(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.If) and self._is_type_checking_guard(node.test):
                for stmt in node.body:
                    if isinstance(stmt, ast.Import):
                        for alias in stmt.names:
                            self._type_checking_names.add(alias.asname or alias.name.split(".")[0])
                    elif isinstance(stmt, ast.ImportFrom):
                        for alias in stmt.names:
                            if alias.name != "*":
                                self._type_checking_names.add(alias.asname or alias.name)

    @staticmethod
    def _annotation_name_refs(ann: ast.AST | None) -> set[str]:
        if ann is None:
            return set()
        return {child.id for child in ast.walk(ann) if isinstance(child, ast.Name)}

    def _iter_annotations(self, node: ast.AST) -> list[tuple[ast.AST, ast.AST]]:
        found: list[tuple[ast.AST, ast.AST]] = []
        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child.returns is not None:
                    found.append((child, child.returns))
                for arg in child.args.posonlyargs + child.args.args + child.args.kwonlyargs:
                    if arg.annotation is not None:
                        found.append((arg, arg.annotation))
                if child.args.vararg and child.args.vararg.annotation is not None:
                    found.append((child.args.vararg, child.args.vararg.annotation))
                if child.args.kwarg and child.args.kwarg.annotation is not None:
                    found.append((child.args.kwarg, child.args.kwarg.annotation))
            elif isinstance(child, ast.AnnAssign) and child.annotation is not None:
                found.append((child, child.annotation))
        return found

    def _check_type_checking_usage(self, tree: ast.AST) -> None:
        if not self._type_checking_names:
            return
        for owner, ann in self._iter_annotations(tree):
            used = self._annotation_name_refs(ann) & self._type_checking_names
            if used:
                first_name = sorted(used)[0]
                self.add_violation(
                    owner,
                    f"❌ [Future Annotations Required] Type '{first_name}' imported under TYPE_CHECKING is used in annotation without 'from __future__ import annotations'.",
                    suggestion="Add 'from __future__ import annotations' at the top of the file or quote the annotation string."
                )
                return

    def _check_class_self_references(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            cls_name = node.name
            for stmt in node.body:
                if isinstance(stmt, ast.ClassDef):
                    continue
                for owner, ann in self._iter_annotations(stmt):
                    if cls_name in self._annotation_name_refs(ann):
                        self.add_violation(
                            owner,
                            f"❌ [Future Annotations Required] Class '{cls_name}' is self-referenced in annotation without 'from __future__ import annotations'.",
                            suggestion="Add 'from __future__ import annotations' at the top of the file to prevent runtime NameError."
                        )
                        return
