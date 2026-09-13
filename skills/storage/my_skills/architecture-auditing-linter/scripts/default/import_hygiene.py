import ast
from default.base import BaseRule


class ImportHygieneRule(BaseRule):
    DEPRECATED_MODULES = {
        "imp": "importlib",
        "optparse": "argparse",
        "formatter": "none (removed in Python 3.10)",
        "parser": "ast",
        "cgi": "none (deprecated in Python 3.11)",
        "cgitb": "none (deprecated in Python 3.11)",
        "telnetlib": "none (deprecated in Python 3.11)",
        "pipes": "shlex",
        "sndhdr": "none (deprecated in Python 3.11)",
        "sunau": "none (deprecated in Python 3.11)",
        "uu": "none (deprecated in Python 3.11)",
        "xdrlib": "none (deprecated in Python 3.11)",
        "aifc": "none (deprecated in Python 3.11)",
        "crypt": "hashlib or secrets",
        "asynchat": "asyncio",
        "asyncore": "asyncio",
    }

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top_level = alias.name.split(".")[0]
            if top_level in self.DEPRECATED_MODULES:
                replacement = self.DEPRECATED_MODULES[top_level]
                self.add_violation(
                    node,
                    f"⚠️ [Import Violation] Deprecated stdlib module '{top_level}' imported.",
                    suggestion=f"Use '{replacement}' instead."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        top_level = module.split(".")[0] if module else ""

        if any(alias.name == "*" for alias in node.names):
            self.add_violation(
                node,
                f"❌ [Import Violation] Wildcard import 'from {module} import *' detected.",
                suggestion="Explicitly import required functions/classes instead of wildcard imports."
            )
            return

        if top_level in self.DEPRECATED_MODULES:
            replacement = self.DEPRECATED_MODULES[top_level]
            self.add_violation(
                node,
                f"⚠️ [Import Violation] Deprecated stdlib module '{top_level}' imported.",
                suggestion=f"Use '{replacement}' instead."
            )

        self.generic_visit(node)
