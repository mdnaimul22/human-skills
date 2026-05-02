import ast
import asyncio
import sys
from pathlib import Path
from helpers.tool import Tool, Response

class Linter(Tool):
    """
    Next-Gen Architecture & Compliance Auditor.
    Enforces project-specific coding standards (Logging, Pathlib, Print, Env, etc.)
    """
    name: str = "linter"
    description: str = "Scans Python projects or files for architecture and coding standard violations."
    arguments: dict = {
        "scan_path": "Path to the project directory or a specific .py file to audit (REQUIRED).",
        "ignored_path": "Comma-separated list of directory names to skip during scanning."
    }
    instruction: str = "Audit your codebase to ensure it follows the unified architecture patterns."

    async def execute(self, **kwargs) -> Response:
        scan_path_str = self.args.get("scan_path") or self.args.get("path")
        
        # --- 1. ARGUMENT VALIDATION ---
        if not scan_path_str:
            return Response(
                message="❌ Error: 'scan_path' argument is required.\n💡 Usage: human-skills '{\"tool_name\": \"linter\", \"tool_args\": {\"scan_path\": \".\"}}'", 
                break_loop=False
            )

        # Catch typos or invalid arguments
        allowed_keys = ["scan_path", "ignored_path", "path", "ignored_apth"]
        invalid_keys = [k for k in self.args.keys() if k not in allowed_keys]
        if invalid_keys:
            msg = f"❌ Error: Invalid argument(s) provided: {', '.join(invalid_keys)}\n"
            msg += f"💡 Available arguments: {', '.join(['scan_path', 'ignored_path'])}"
            return Response(message=msg, break_loop=False)

        scan_path = Path(scan_path_str).resolve()
        if not scan_path.exists():
            return Response(message=f"❌ Error: Path '{scan_path}' does not exist.", break_loop=False)

        # --- 2. SETUP IGNORES ---
        custom_ignores = self.args.get("ignored_path") or self.args.get("ignored_apth") or ""
        ignored_list = {i.strip() for i in custom_ignores.split(",") if i.strip()}
        
        # Default bypass directories from architecture rules
        bypass_dirs = {
            "src/config", "tests", ".agents", ".a0proj", ".claude", ".gemini", 
            "venv", ".venv", "__pycache__", ".git", "scripts", "docs"
        }
        bypass_dirs.update(ignored_list)

        # --- 3. EXECUTE AUDIT ---
        violations_count, report = self.audit_project(scan_path, bypass_dirs)

        # --- 4. FORMAT RESPONSE ---
        status = "✨ CLEAN ARCHITECTURE! No violations detected." if violations_count == 0 else f"🚨 Audit finished. Found {violations_count} compliance violations."
        
        full_message = f"🚀 Starting human-lint (Next-Gen) on: {scan_path}\n"
        full_message += "=" * 65 + "\n"
        full_message += report
        full_message += "=" * 65 + "\n"
        full_message += f"{status}\n"
        
        if violations_count > 0:
            full_message += "💡 Tip: Review the violations above and refactor to follow the Project Coding Standards."

        return Response(message=full_message, break_loop=False)

    def audit_project(self, target_path: Path, bypass_dirs: set[str]):
        if target_path.is_file():
            py_files = [target_path]
            root_dir = target_path.parent
        else:
            py_files = list(target_path.rglob("*.py"))
            root_dir = target_path

        total_violations = 0
        report_lines = []

        for py_file in sorted(py_files):
            rel_path = py_file.relative_to(root_dir)
            
            # Ignore hidden files, virtualenvs, and explicitly bypassed dirs
            is_bypassed = any(str(rel_path).startswith(d) for d in bypass_dirs) or \
                          any(part.startswith(".") for part in py_file.parts) or \
                          any(part in ("venv", ".venv", "__pycache__", ".git") for part in py_file.parts)

            if is_bypassed:
                if not (target_path.is_file() and py_file == target_path): # Allow if scanning the file directly
                    continue

            if py_file.suffix != ".py":
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
                    report_lines.append(f"\n📄 {py_file.relative_to(root_dir) if not target_path.is_file() else py_file.name}")
                    for v in auditor.violations:
                        report_lines.append(f"  {v}")
                    total_violations += len(auditor.violations)
            except Exception as e:
                report_lines.append(f"⚠️ Error parsing {py_file}: {e}")

        return total_violations, "\n".join(report_lines) + "\n"

class CodeAuditor(ast.NodeVisitor):
    def __init__(self, filename: Path, root_dir: Path, bypass_dirs: set[str]):
        self.filename = filename
        self.violations = []
        # Check if the file itself is in a bypass directory or is a config file
        self.is_config_file = any(d in str(filename) for d in bypass_dirs)

    def add_violation(self, node, message):
        self.violations.append(f"L{node.lineno}: {message}")

    def visit_Import(self, node):
        for alias in node.names:
            # Rule 1: Logging Violation
            if alias.name == "logging" or alias.name.startswith("logging."):
                self.add_violation(node, "❌ [Logging Violation] Direct 'import logging' used. Use 'setup_logger' instead.")
            # Rule 2: Pathlib Violation
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
        # Rule 5: Print Statement
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.add_violation(node, "⚠️ [Print Statement] Manual 'print()' found. Use a logger for production code.")

        # Rule 3: Manual Directory Creation
        for keyword in node.keywords:
            if keyword.arg == "exist_ok" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                self.add_violation(node, "❌ [Manual Dir Creation] 'exist_ok=True' found. Use 'ensure_dir' from config instead.")

        # Rule 6: Direct Env Access
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr in ("getenv", "getenvb"):
                self.add_violation(node, "❌ [Env Access] Direct 'os.getenv()' used. Use 'Settings' class.")
        
        # Rule 7: Logger Compliance
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
        # Rule 4: Silent Exception
        for handler in node.handlers:
            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                self.add_violation(handler, "❌ [Silent Exception] 'except: pass' found. Do not swallow exceptions silently.")
        self.generic_visit(node)
