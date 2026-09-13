import ast
from default.base import BaseRule


class MemoryEfficiencyRule(BaseRule):
    GENERATOR_FRIENDLY_FUNCS = {"sum", "any", "all", "min", "max", "join"}

    def __init__(self, context):
        super().__init__(context)
        self._inside_loop = False

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
                    suggestion="Repeated string concatenation creates intermediate strings with O(N^2) memory reallocations. Accumulate in a list and use str.join()."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
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
                    suggestion=f"Use a generator expression '{func_name}(...)' without square brackets to stream items without allocating a full list in memory."
                )

        self.generic_visit(node)
