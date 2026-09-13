import ast
from default.base import BaseRule, FileContext


class KillSwitchRule(BaseRule):
    def __init__(self, context: FileContext):
        super().__init__(context)
        self._has_kill_pid = False
        self._has_uvicorn_run = False
        self._uvicorn_node: ast.Call | None = None

    def visit_Call(self, node: ast.Call) -> None:
        if self.ctx.is_main_file:
            if isinstance(node.func, ast.Name) and node.func.id == "kill_pid":
                self._has_kill_pid = True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "uvicorn":
                    self._has_uvicorn_run = True
                    self._uvicorn_node = node

        self.generic_visit(node)

    def post_check(self) -> None:
        if self.ctx.is_main_file and self._has_uvicorn_run and not self._has_kill_pid and self._uvicorn_node:
            self.add_violation(
                self._uvicorn_node,
                "❌ [Kill Switch Missing] 'uvicorn.run()' found without 'kill_pid(port)'. "
                "Add 'kill_pid(port)' before uvicorn.run() to prevent 'Address already in use' errors."
            )
