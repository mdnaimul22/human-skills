import ast
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from helpers.tool import Tool, Response

class Linter(Tool):
    """
    Next-Gen Architecture & Compliance Auditor.
    Enforces project-specific coding standards and generates refactoring task lists.
    """
    name: str = "linter"
    description: str = "Scans Python projects for architecture violations and generates a REFACTORING_TASKS.md report."
    arguments: dict = {
        "scan_path": "Path to the project directory or a specific .py file to audit (REQUIRED).",
        "ignored_path": "Comma-separated list of directory names to skip during scanning."
    }
    instruction: str = "Audit your codebase and generate a tracked task list for refactoring."

    async def execute(self, **kwargs) -> Response:
        scan_path_str = self.args.get("scan_path") or self.args.get("path")
        
        if not scan_path_str:
            return Response(
                message="❌ Error: 'scan_path' argument is required.\n💡 Usage: human-skills '{\"tool_name\": \"linter\", \"tool_args\": {\"scan_path\": \".\"}}'", 
                break_loop=False
            )

        allowed_keys = ["scan_path", "ignored_path", "path", "ignored_apth"]
        invalid_keys = [k for k in self.args.keys() if k not in allowed_keys]
        if invalid_keys:
            msg = f"❌ Error: Invalid argument(s) provided: {', '.join(invalid_keys)}\n"
            msg += f"💡 Available arguments: {', '.join(['scan_path', 'ignored_path'])}"
            return Response(message=msg, break_loop=False)

        scan_path = Path(scan_path_str).resolve()
        if not scan_path.exists():
            return Response(message=f"❌ Error: Path '{scan_path}' does not exist.", break_loop=False)

        custom_ignores = self.args.get("ignored_path") or self.args.get("ignored_apth") or ""
        ignored_list = {i.strip() for i in custom_ignores.split(",") if i.strip()}
        
        bypass_dirs = {
            "src/config", "tests", ".agents", ".a0proj", ".claude", ".gemini", 
            "venv", ".venv", "__pycache__", ".git", "scripts", "docs"
        }
        bypass_dirs.update(ignored_list)

        # --- AUDIT ---
        audit_results = self.audit_project(scan_path, bypass_dirs)
        total_violations = sum(len(v) for v in audit_results.values())

        # --- CONSOLE REPORT ---
        status = "✨ CLEAN ARCHITECTURE! No violations detected." if total_violations == 0 else f"🚨 Audit finished. Found {total_violations} compliance violations."
        
        console_msg = f"🚀 Starting human-lint (Next-Gen) on: {scan_path}\n"
        console_msg += "=" * 65 + "\n"
        
        for file_path, violations in audit_results.items():
            console_msg += f"\n📄 {file_path}\n"
            for v in violations:
                console_msg += f"  {v}\n"
        
        console_msg += "=" * 65 + "\n"
        console_msg += f"{status}\n"

        # --- GENERATE MARKDOWN TASK LIST ---
        if total_violations > 0 and scan_path.is_dir():
            report_path = scan_path / "REFACTORING_TASKS.md"
            self.generate_markdown_report(report_path, scan_path, audit_results)
            console_msg += f"📝 Task list generated: {report_path.name}\n"
            console_msg += "💡 Tip: Open the markdown file to track your refactoring progress."

        return Response(message=console_msg, break_loop=False)

    def audit_project(self, target_path: Path, bypass_dirs: set[str]) -> dict:
        if target_path.is_file():
            py_files = [target_path]
            root_dir = target_path.parent
        else:
            py_files = list(target_path.rglob("*.py"))
            root_dir = target_path

        results = {}

        for py_file in sorted(py_files):
            rel_path = py_file.relative_to(root_dir)
            is_bypassed = any(str(rel_path).startswith(d) for d in bypass_dirs) or \
                          any(part.startswith(".") for part in py_file.parts) or \
                          any(part in ("venv", ".venv", "__pycache__", ".git") for part in py_file.parts)

            if is_bypassed and not (target_path.is_file() and py_file == target_path):
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
                    results[str(rel_path)] = auditor.violations
            except Exception as e:
                results[str(rel_path)] = [f"⚠️ Error parsing file: {e}"]

        return results

    def generate_markdown_report(self, report_path: Path, root_dir: Path, results: dict):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = [
            f"# 🏗️ Refactoring Tasks: {root_dir.name}",
            f"> Generated by **human-skills** on {now}",
            "\n## Summary",
            f"- **Project Directory:** `{root_dir}`",
            f"- **Total Violations:** {sum(len(v) for v in results.values())}",
            f"- **Files to Refactor:** {len(results)}",
            "\n---\n"
        ]

        # Group by directory
        grouped = {}
        for file_path, violations in results.items():
            dir_name = str(Path(file_path).parent)
            if dir_name not in grouped:
                grouped[dir_name] = []
            grouped[dir_name].append((file_path, violations))

        for dir_name, files in sorted(grouped.items()):
            dir_label = "📁 Root" if dir_name == "." else f"📁 {dir_name}"
            content.append(f"### {dir_label}")
            for file_path, violations in files:
                file_name = Path(file_path).name
                content.append(f"#### 📄 {file_name}")
                for v in violations:
                    # Transform L123: Message to - [ ] L123: Message
                    task = v.replace("❌ ", "").replace("⚠️ ", "")
                    content.append(f"- [ ] {task}")
            content.append("")

        report_path.write_text("\n".join(content), encoding="utf-8")

class CodeAuditor(ast.NodeVisitor):
    def __init__(self, filename: Path, root_dir: Path, bypass_dirs: set[str]):
        self.filename = filename
        self.violations = []
        self.is_config_file = any(d in str(filename) for d in bypass_dirs)

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
