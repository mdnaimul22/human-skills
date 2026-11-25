import ast
from default.base import BaseRule, FileContext


class PathSafetyRule(BaseRule):
    STRICT_PATH_METHODS = {
        "read_text": "read_text",
        "read_bytes": "read_bytes",
        "write_text": "write_text",
        "write_bytes": "write_bytes",
        "mkdir": "ensure_dir",
        "iterdir": "list_files",
        "glob": "list_files",
        "rglob": "list_files",
    }

    GENERIC_PATH_METHODS = {
        "exists": "exists",
        "is_file": "is_file",
        "is_dir": "is_dir",
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

    PATH_CONSTRUCTORS = {"Path", "PurePath", "PosixPath", "WindowsPath"}
    PATH_VAR_SUFFIXES = ("_path", "_dir", "_file", "filepath", "dirpath")
    NON_PATH_RECEIVERS = {
        "redis", "redis_client", "cache", "client", "repo", "repository",
        "session", "db", "stmt", "query", "queryset", "resolver", "dns",
        "future", "promise", "container", "account", "user", "model",
    }

    def __init__(self, context: FileContext):
        super().__init__(context)
        self._path_vars: set[str] = set()
        self._os_path_aliases: set[str] = set()
        self._list_files_vars: set[str] = set()
        self._list_files_collections: set[str] = set()
        self._docstring_ids: set[int] = set()
        self._route_str_ids: set[int] = set()
        self._pathlib_imported: bool = False

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        self._pre_scan(tree)
        return super().run(tree)

    def _pre_scan(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    if isinstance(node.body[0].value.value, str):
                        self._docstring_ids.add(id(node.body[0].value))
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call):
                            for arg in dec.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    self._route_str_ids.add(id(arg))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "pathlib":
                        self._pathlib_imported = True
                    elif alias.name == "os.path":
                        self._os_path_aliases.add(alias.asname or "os.path")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "pathlib":
                    self._pathlib_imported = True
                elif node.module == "os":
                    for alias in node.names:
                        if alias.name == "path":
                            self._os_path_aliases.add(alias.asname or "path")
            elif isinstance(node, ast.Assign):
                if self._is_path_expr(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self._path_vars.add(target.id)
                elif self._is_list_files_call(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self._list_files_collections.add(target.id)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                if self._is_list_files_iter(node.iter) and isinstance(node.target, ast.Name):
                    self._list_files_vars.add(node.target.id)
            elif isinstance(node, ast.comprehension):
                if self._is_list_files_iter(node.iter) and isinstance(node.target, ast.Name):
                    self._list_files_vars.add(node.target.id)

    def _is_list_files_call(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False
        if isinstance(node.func, ast.Name) and node.func.id == "list_files":
            return True
        return isinstance(node.func, ast.Attribute) and node.func.attr == "list_files"

    def _is_list_files_iter(self, node: ast.AST) -> bool:
        if self._is_list_files_call(node):
            return True
        if isinstance(node, ast.Name) and node.id in self._list_files_collections:
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("sorted", "reversed", "list"):
            return bool(node.args and self._is_list_files_iter(node.args[0]))
        return False

    def _is_path_expr(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self.PATH_CONSTRUCTORS:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in self.PATH_CONSTRUCTORS:
                return True
            if isinstance(node.func, ast.Attribute) and self._is_path_expr(node.func.value):
                return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return self._is_path_expr(node.left) or self._is_settings_path(node.left)
        if isinstance(node, ast.Attribute):
            if self._is_settings_path(node):
                return True
            if node.attr in ("parent", "parents") and self._is_path_expr(node.value):
                return True
        if isinstance(node, ast.Name) and node.id in self._path_vars:
            return True
        return False

    def _is_settings_path(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "Settings" and node.attr.endswith(("_DIR", "_PATH", "_FILE")):
                return True
        return False

    def _is_likely_path_receiver(self, node: ast.AST) -> bool:
        if self._is_path_expr(node):
            return True
        if isinstance(node, ast.Name):
            low = node.id.lower()
            if low in self.NON_PATH_RECEIVERS:
                return False
            if low in ("path", "p") and self._pathlib_imported:
                return True
            if low.endswith(self.PATH_VAR_SUFFIXES):
                return True
        if isinstance(node, ast.Attribute):
            low = node.attr.lower()
            if low.endswith(self.PATH_VAR_SUFFIXES):
                return True
        return False

    def _is_os_path_target(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "os" and node.attr == "path":
                return True
        if isinstance(node, ast.Name) and node.id in self._os_path_aliases:
            return True
        return False

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
            if id(node) not in self._docstring_ids and id(node) not in self._route_str_ids:
                val = node.value.strip()
                if val == "/tmp" or val.startswith("/tmp/"):
                    self.add_violation(
                        node,
                        f"❌ [Path Safety Violation] Direct usage of system '/tmp' detected ('{val}').",
                        suggestion="Use project-scoped sandboxed directory 'data/tmp' (via src.config) instead of system '/tmp' to prevent file collisions, security leaks, and sandbox escapes.",
                    )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if not self.ctx.is_config_file:
            if node.attr in self.OS_PATH_BLACKLIST and self._is_os_path_target(node.value):
                suggestion = self.OS_PATH_BLACKLIST[node.attr]
                self.add_violation(node, f"❌ [Config Path Violation] 'os.path.{node.attr}' used. Use '{suggestion}' from files.py instead.")
                self.generic_visit(node)
                return

            if node.attr in self.STRICT_PATH_METHODS:
                suggestion = self.STRICT_PATH_METHODS[node.attr]
                self.add_violation(node, f"❌ [Config Path Violation] Direct '.{node.attr}()' used. Use '{suggestion}' from src.config.files instead.")
            elif node.attr in self.GENERIC_PATH_METHODS:
                if node.attr in ("is_dir", "is_file") and isinstance(node.value, ast.Name) and node.value.id in self._list_files_vars:
                    self.generic_visit(node)
                    return
                if self._is_likely_path_receiver(node.value):
                    suggestion = self.GENERIC_PATH_METHODS[node.attr]
                    self.add_violation(node, f"❌ [Config Path Violation] Direct '.{node.attr}()' used. Use '{suggestion}' from src.config.files instead.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not self.ctx.is_config_file:
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "tempfile":
                self.add_violation(
                    node,
                    f"❌ [Path Safety Violation] 'tempfile.{node.func.attr}()' used.",
                    suggestion="Use project-scoped sandboxed directory 'data/tmp' (via src.config.ensure_dir) instead of system temporary directories.",
                )
            func_name = node.func.attr if isinstance(node.func, ast.Attribute) else (node.func.id if isinstance(node.func, ast.Name) else "")
            if func_name in ("mkdir", "makedirs"):
                for keyword in node.keywords:
                    if keyword.arg == "exist_ok" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        self.add_violation(node, "❌ [Manual Dir Creation] 'exist_ok=True' found. Use 'ensure_dir' from config instead.")
        self.generic_visit(node)
