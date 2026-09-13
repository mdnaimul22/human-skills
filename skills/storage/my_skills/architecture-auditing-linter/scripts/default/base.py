import ast
from pathlib import Path


class FileContext:
    def __init__(self, filename: Path, root_dir: Path, bypass_dirs: set[str], content: str = ""):
        self.filename = filename
        self.root_dir = root_dir
        self.bypass_dirs = bypass_dirs
        self.content = content
        self.rel_path = filename.relative_to(root_dir)
        in_config_dir = "config" in filename.parts
        _pathlib_exempt = {"paths.py", "files.py", "logger.py", "dotenv.py", "__init__.py", "settings.py"}
        self.is_config_file = filename.name in _pathlib_exempt and in_config_dir
        self.is_settings_file = filename.name == "settings.py" and in_config_dir
        self.is_helpers_file = "helpers" in filename.parts
        self.is_db_file = "db" in filename.parts or filename.name == "connection.py"
        self.is_main_file = filename.name == "main.py"


class BaseRule(ast.NodeVisitor):
    def __init__(self, context: FileContext):
        self.ctx = context
        self.violations: list[str] = []
        self.advisories: list[str] = []

    def add_violation(self, target: ast.AST | int, message: str, suggestion: str | None = None) -> None:
        lineno = target.lineno if isinstance(target, ast.AST) else int(target)
        formatted = f"L{lineno}: {message}"
        if suggestion:
            formatted += f"\n       💡 Fix: {suggestion}"
        self.violations.append(formatted)

    def add_advisory(self, message: str) -> None:
        self.advisories.append(message)

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        self.visit(tree)
        self.post_check()
        return self.violations, self.advisories

    def post_check(self) -> None:
        pass
