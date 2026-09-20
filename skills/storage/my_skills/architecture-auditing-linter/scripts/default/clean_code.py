import ast
import io
import tokenize
from default.base import BaseRule


class CleanCodeRule(BaseRule):
    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            clean_preview = node.value.value.strip().replace("\n", " ")[:50]
            self.add_violation(
                node,
                f"❌ [Clean Code Violation] Docstring or standalone string detected ('{clean_preview}...').",
                suggestion="Docstrings and standalone comment strings are prohibited inside implementation code (Rule 10). Code must be self-documenting through precise types, clean architecture, and explicit naming. Remove docstrings to conserve token context.",
            )
        self.generic_visit(node)

    def post_check(self) -> None:
        if not self.ctx.content:
            return
        try:
            tokens = tokenize.tokenize(io.BytesIO(self.ctx.content.encode("utf-8")).readline)
            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    if tok.start[0] == 1 and tok.string.startswith("#!"):
                        continue
                    line_before = tok.line[:tok.start[1]].strip()
                    if not line_before:
                        comment_preview = tok.string.strip().replace("\n", " ")[:50]
                        self.add_violation(
                            tok.start[0],
                            f"❌ [Clean Code Violation] Standalone/top-level comment line detected ('{comment_preview}').",
                            suggestion="Standalone comment blocks and header comments are forbidden (Rule 10). Keep code clean and self-explanatory. Only brief, essential trailing inline comments ('code  # info') are allowed.",
                        )
        except tokenize.TokenError:
            pass
