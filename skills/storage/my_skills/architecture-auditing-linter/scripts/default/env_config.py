import ast
from default.base import BaseRule, FileContext


class EnvConfigRule(BaseRule):
    def __init__(self, context: FileContext):
        super().__init__(context)
        self.has_settings_defaults = False

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "environ":
            if not self.ctx.is_config_file and not self.ctx.is_helpers_file:
                self.add_violation(node, "❌ [Env Access] Direct 'os.environ' used. Use 'Settings' class.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr in ("getenv", "getenvb"):
                self.add_violation(node, "❌ [Env Access] Direct 'os.getenv()' used. Use 'Settings' class.")
                if len(node.args) >= 2 or any(kw.arg == "default" for kw in node.keywords):
                    self.add_violation(node, "⚠️ [Silent Default] os.getenv() with fallback default found. Use Settings class — missing env vars should fail loudly.")

        if self.ctx.is_settings_file and isinstance(node.func, ast.Name) and node.func.id == "Field":
            for kw in node.keywords:
                if kw.arg == "default" and isinstance(kw.value, ast.Constant):
                    if kw.value.value not in (None, ""):
                        self.has_settings_defaults = True

        self.generic_visit(node)

    def post_check(self) -> None:
        if self.ctx.is_settings_file and self.has_settings_defaults:
            self.add_advisory(
                "⚠️ [Settings Advisory] Critical and environment-specific parameters must be controlled via .env. "
                "Only safe, non-breaking fallback values should be defined as defaults in Settings."
            )
