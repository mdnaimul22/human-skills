import ast
from default.base import BaseRule


class PathSafetyRule(BaseRule):
    FORBIDDEN_PATH_METHODS = {
        "exists": "exists",
        "is_file": "is_file",
        "is_dir": "is_dir",
        "read_text": "read_text",
        "read_bytes": "read_text",
        "write_text": "write_text",
        "write_bytes": "write_text",
        "mkdir": "ensure_dir",
        "iterdir": "list_files",
        "glob": "list_files",
        "rglob": "list_files",
        "unlink": "delete",
        "resolve": "get_abs_path",
        "absolute": "get_abs_path",
    }

    OS_PATH_BLACKLIST = {
        "realpath": "get_abs_path",
        "exists": "exists",
        "isdir": "is_dir",
        "join": "get_abs_path or relative string concatenation",
    }

    def visit_Import(self, node: ast.Import) -> None:
        if not self.ctx.is_config_file:
            for alias in node.names:
                if alias.name == "pathlib":
                    self.add_violation(node, "❌ [Pathlib Violation] Direct 'import pathlib' used outside config. Use 'src.config' utilities.")
                if alias.name == "tempfile":
                    self.add_violation(
                        node,
                        "❌ [Path Safety Violation] Direct 'import tempfile' used outside config.",
                        suggestion="Use project-scoped sandboxed directory 'data/tmp' (via src.config) instead of system temporary files.",
                    )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if not self.ctx.is_config_file:
            if node.module == "pathlib":
                self.add_violation(node, "❌ [Pathlib Violation] Direct 'pathlib' import used outside config. Use 'src.config' utilities.")
            if node.module == "tempfile":
                self.add_violation(
                    node,
                    "❌ [Path Safety Violation] 'from tempfile import ...' used outside config.",
                    suggestion="Use project-scoped sandboxed directory 'data/tmp' (via src.config) instead of system temporary files.",
                )
            if node.module == "os.path":
                for alias in node.names:
                    if alias.name in self.OS_PATH_BLACKLIST:
                        suggestion = self.OS_PATH_BLACKLIST[alias.name]
                        self.add_violation(node, f"❌ [Config Path Violation] 'from os.path import {alias.name}' used. Use '{suggestion}' from files.py instead.")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if not self.ctx.is_config_file and isinstance(node.value, str):
            val = node.value.strip()
            if val == "/tmp" or val.startswith("/tmp/") or "/tmp/" in val:
                self.add_violation(
                    node,
                    f"❌ [Path Safety Violation] Direct usage of system '/tmp' detected ('{val}').",
                    suggestion="Use project-scoped sandboxed directory 'data/tmp' (via src.config) instead of system '/tmp' to prevent file collisions, security leaks, and sandbox escapes.",
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if not self.ctx.is_config_file:
            if node.attr in self.FORBIDDEN_PATH_METHODS:
                suggestion = self.FORBIDDEN_PATH_METHODS[node.attr]
                self.add_violation(node, f"❌ [Config Path Violation] Direct '.{node.attr}()' used. Use '{suggestion}' from src.config.files instead.")

            if node.attr in self.OS_PATH_BLACKLIST:
                is_os_path = False
                if isinstance(node.value, ast.Name) and node.value.id in ("os", "path"):
                    is_os_path = True
                elif isinstance(node.value, ast.Attribute) and node.value.attr == "path":
                    is_os_path = True

                if is_os_path:
                    suggestion = self.OS_PATH_BLACKLIST[node.attr]
                    self.add_violation(node, f"❌ [Config Path Violation] 'os.path.{node.attr}' used. Use '{suggestion}' from files.py instead.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not self.ctx.is_config_file:
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "tempfile":
                self.add_violation(
                    node,
                    f"❌ [Path Safety Violation] 'tempfile.{node.func.attr}()' used.",
                    suggestion="Use project-scoped sandboxed directory 'data/tmp' (via src.config.ensure_dir) instead of system temporary directories.",
                )
        for keyword in node.keywords:
            if keyword.arg == "exist_ok" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                self.add_violation(node, "❌ [Manual Dir Creation] 'exist_ok=True' found. Use 'ensure_dir' from config instead.")
        self.generic_visit(node)
