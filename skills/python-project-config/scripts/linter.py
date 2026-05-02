import ast
import asyncio
from pathlib import Path
from helpers.tool import Tool, Response

class Linter(Tool):
    """
    Next-Gen Architecture Auditor.
    Scans Python files for violations of clean architecture and coding standards.
    """
    name: str = "linter"
    description: str = "Scans a project for architecture and coding standard violations (logging, pathlib, print, etc.)"
    arguments: str = "{'scan_path': '/path/to/scan', 'ignored_path': 'comma,separated,dirs'}"

    async def execute(self, **kwargs) -> Response:
        scan_path_str = self.args.get("scan_path") or self.args.get("path")
        if not scan_path_str:
            return Response(message="❌ Error: 'scan_path' is required.", break_loop=True)

        scan_path = Path(scan_path_str).resolve()
        if not scan_path.exists():
            return Response(message=f"❌ Error: Path '{scan_path}' does not exist.", break_loop=True)

        # Custom ignored paths from user
        custom_ignores = self.args.get("ignored_path") or self.args.get("ignored_apth") or ""
        ignored_list = {i.strip() for i in custom_ignores.split(",") if i.strip()}
        
        # Default bypass directories
        bypass_dirs = {"src/config", "tests", ".agents", ".a0proj", ".claude", ".gemini", "venv", ".venv", "__pycache__", ".git"}
        bypass_dirs.update(ignored_list)

        violations_count, report = self.audit_project(scan_path, bypass_dirs)

        status = "✨ CLEAN ARCHITECTURE! No violations detected." if violations_count == 0 else f"🚨 Audit finished. Found {violations_count} compliance violations."
        
        full_message = f"🚀 Starting human-lint on: {scan_path}\n"
        full_message += "=" * 60 + "\n"
        full_message += report
        full_message += "=" * 60 + "\n"
        full_message += status

        return Response(message=full_message, break_loop=False)

    def audit_project(self, root_dir: Path, bypass_dirs: set[str]):
        py_files = list(root_dir.rglob("*.py"))
        total_violations = 0
        report_lines = []

        for py_file in sorted(py_files):
            # Ignore directories
            if any(part in bypass_dirs or part in (".git", "__pycache__", "venv", ".venv") for part in py_file.parts):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        continue
                    tree = ast.parse(content)
                
                auditor = CodeAuditor(py_file, root_dir, bypass_dirs)
                auditor.visit(tree)
                
                if auditor.violations:
                    report_lines.append(f"\n📄 {py_file.relative_to(root_dir)}")
                    for v in auditor.violations:
                        report_lines.append(f"  {v}")
                    total_violations += len(auditor.violations)
            except Exception as e:
                report_lines.append(f"⚠️ Error parsing {py_file}: {e}")

        return total_violations, "\n".join(report_lines) + "\n"

class CodeAuditor(ast.NodeVisitor):
    def __init__(self, filename: Path, root_dir: Path, bypass_dirs: set[str]):
        self.filename = filename
        self.rel_path = filename.relative_to(root_dir)
        self.violations = []
        self.is_config_file = any(d in str(self.rel_path) for d in bypass_dirs)

    def add_violation(self, node, message):
        self.violations.append(f"L{node.lineno}: {message}")

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "logging" or alias.name.startswith("logging."):
                self.add_violation(node, "❌ [Logging Violation] Direct 'import logging' used. Use 'setup_logger' instead.")
            if alias.name == "pathlib" and not self.is_config_file:
                self.add_violation(node, "❌ [Pathlib Violation] Direct 'import pathlib' used outside config. Use 'src.config' utilities.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module == "logging" or (node.module and node.module.startswith("logging.")):
            self.add_violation(node, "❌ [Logging Violation] Direct 'logging' import used. Use 'setup_logger' instead.")
        if node.module == "pathlib" and not self.is_config_file:
            self.add_violation(node, "❌ [Pathlib Violation] Direct 'pathlib' import used outside config. Use 'src.config' utilities.")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.add_violation(node, "⚠️ [Print Statement] Manual 'print()' found. Use a logger for production code.")

        for keyword in node.keywords:
            if keyword.arg == "exist_ok" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                self.add_violation(node, "❌ [Manual Dir Creation] 'exist_ok=True' found. Use 'ensure_dir' from config instead.")

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr in ("getenv", "getenvb"):
                self.add_violation(node, "❌ [Env Access] Direct 'os.getenv()' used. Use 'Settings' class.")
        
        if isinstance(node.func, ast.Name) and node.func.id == "setup_logger":
            if node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                     self.add_violation(node, f"❌ [Logger Compliance] Hardcoded log filename '{arg.value}' found. Use 'Settings.LOG_DIR / \"layer.log\"'.")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "environ":
            self.add_violation(node, "❌ [Env Access] Direct 'os.environ' used. Use 'Settings' class.")
        self.generic_visit(node)

    def visit_Try(self, node):
        for handler in node.handlers:
            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                self.add_violation(handler, "❌ [Silent Exception] 'except: pass' found. Do not swallow exceptions silently.")
        self.generic_visit(node)
