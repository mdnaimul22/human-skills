import ast
from default.base import BaseRule


class MemoryEfficiencyRule(BaseRule):
    GENERATOR_FRIENDLY_FUNCS = {"sum", "any", "all", "min", "max", "join"}
    PYDANTIC_BASE_NAMES = {"BaseModel", "BaseSettings"}

    def __init__(self, context):
        super().__init__(context)
        self._inside_loop = False

    def _is_pydantic_model(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in self.PYDANTIC_BASE_NAMES or base.id.endswith(("BaseModel", "BaseSettings", "Schema", "Model")):
                    return True
            elif isinstance(base, ast.Attribute):
                if base.attr in self.PYDANTIC_BASE_NAMES or base.attr.endswith(("BaseModel", "BaseSettings")):
                    return True
        return False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self._is_pydantic_model(node):
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

    def visit_For(self, node: ast.For) -> None:
        self._inside_loop = True
        self.generic_visit(node)
        self._inside_loop = False

    def visit_While(self, node: ast.While) -> None:
        self._inside_loop = True
        self.generic_visit(node)
        self._inside_loop = False

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if self._inside_loop and isinstance(node.op, ast.Add):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
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
                if caller.func.attr in {"model_dump", "dict"}:
                    caller_str = ast.unparse(caller)
                    self.add_violation(
                        node,
                        f"⚠️ [Memory & CPU Inefficiency] Calling '.get()' on serialized Pydantic model ('{caller_str}.get(...)').",
                        suggestion=(
                            f"Serializing the entire model to a dictionary via '{caller.func.attr}()' just to access a single field "
                            f"allocates heap memory for all fields and wastes CPU cycles. Access the field directly: 'model.<field>'."
                        ),
                    )

        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in self.GENERATOR_FRIENDLY_FUNCS and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.ListComp):
                self.add_violation(
                    node,
                    f"⚠️ [Memory Optimization] List comprehension passed to '{func_name}()'.",
                    suggestion=f"Use a generator expression '{func_name}(...)' without square brackets to stream items without allocating a full list in memory.",
                )

        self.generic_visit(node)
