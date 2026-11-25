import ast
from default.base import BaseRule, FileContext


class MemoryEfficiencyRule(BaseRule):
    GENERATOR_FRIENDLY_FUNCS = {"sum", "any", "all", "min", "max"}
    PYDANTIC_BASE_NAMES = {"BaseModel", "BaseSettings"}

    def __init__(self, context: FileContext):
        super().__init__(context)
        self._loop_local_stack: list[set[str]] = []
        self._imports_pydantic = False
        self._pydantic_classes: set[str] = set(self.PYDANTIC_BASE_NAMES)

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name.startswith("pydantic") for a in node.names):
                    self._imports_pydantic = True
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("pydantic"):
                    self._imports_pydantic = True
        return super().run(tree)

    def _is_pydantic_model(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in self._pydantic_classes:
                    return True
                if self._imports_pydantic and base.id.endswith(("BaseModel", "BaseSettings")):
                    return True
            elif isinstance(base, ast.Attribute):
                if base.attr in self.PYDANTIC_BASE_NAMES or base.attr.endswith(("BaseModel", "BaseSettings")):
                    return True
        return False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self._is_pydantic_model(node):
            self._pydantic_classes.add(node.name)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name in {"get", "__getitem__"}:
                        self.add_violation(
                            item,
                            f"❌ [Anti-Pattern Violation] Dictionary-like '{item.name}()' method defined on Pydantic model '{node.name}'.",
                            suggestion=(
                                f"Pydantic models are strongly-typed data contracts, not dictionaries. "
                                f"Access attributes directly via 'model.<field>' or eliminate None at boundary. "
                                f"Defining '{item.name}()' bypasses static typing and creates unnecessary dynamic lookup overhead."
                            ),
                        )
        self.generic_visit(node)

    def _visit_loop(self, node: ast.For | ast.AsyncFor | ast.While) -> None:
        self._loop_local_stack.append(set())
        self.generic_visit(node)
        self._loop_local_stack.pop()

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._loop_local_stack:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._loop_local_stack[-1].add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._loop_local_stack and isinstance(node.target, ast.Name) and node.value is not None:
            self._loop_local_stack[-1].add(node.target.id)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if self._loop_local_stack and isinstance(node.op, ast.Add):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                is_loop_local = (
                    isinstance(node.target, ast.Name)
                    and any(node.target.id in frame for frame in self._loop_local_stack)
                )
                if not is_loop_local:
                    self.add_violation(
                        node,
                        "⚠️ [Memory Optimization] In-place string concatenation ('+=') inside loop detected.",
                        suggestion="Repeated string concatenation creates intermediate strings with O(N^2) memory reallocations. Accumulate in a list and use str.join().",
                    )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            caller = node.func.value
            if isinstance(caller, ast.Call) and isinstance(caller.func, ast.Attribute):
                method_name = caller.func.attr
                is_pydantic_dump = method_name == "model_dump" or (method_name == "dict" and self._imports_pydantic)
                has_serialization_opts = any(kw.arg in ("by_alias", "mode") for kw in caller.keywords)
                if is_pydantic_dump and not has_serialization_opts:
                    caller_str = ast.unparse(caller)
                    self.add_violation(
                        node,
                        f"⚠️ [Memory & CPU Inefficiency] Calling '.get()' on serialized Pydantic model ('{caller_str}.get(...)').",
                        suggestion=(
                            f"Serializing the entire model to a dictionary via '{method_name}()' just to access a single field "
                            f"allocates heap memory for all fields and wastes CPU cycles. Access the field directly: 'model.<field>'."
                        ),
                    )

        if isinstance(node.func, ast.Name) and node.func.id in self.GENERATOR_FRIENDLY_FUNCS and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.ListComp):
                self.add_violation(
                    node,
                    f"⚠️ [Memory Optimization] List comprehension passed to '{node.func.id}()'.",
                    suggestion=f"Use a generator expression '{node.func.id}(...)' without square brackets to stream items without allocating a full list in memory.",
                )

        self.generic_visit(node)
