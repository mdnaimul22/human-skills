import ast
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from helpers.tool import Tool, Response

class Linter(Tool):
    """
    Enforces project-specific coding standards and generates refactoring task lists.
    """
    name: str = "linter"
    description: str = "Scans Python projects for architecture violations. Supports multiple linter types: 'default' (AST-based architecture audit) and 'rest_api' (REST API quality scoring)."
    arguments: dict = {
        "scan_path": "Path to the project directory or a specific .py file to audit (REQUIRED).",
        "linter_type": "Linter mode: 'default' (architecture violations) or 'rest_api' (API quality score). Defaults to 'default'.",
        "ignored_path": "Comma-separated list of directory names to skip during scanning.",
        "ignored_rules": "Comma-separated list of analyzer names to skip (e.g. 'auth_implementation,rate_limiting'). Used only in rest_api mode."
    }
    instruction: str = "Audit your codebase. Use linter_type='default' for architecture violations, 'rest_api' for REST API quality scoring."

    # Infrastructure config files — these USE pathlib/logging by design, always skip them
    CONFIG_INFRA_FILES: set = {"paths.py", "files.py", "logger.py", "dotenv.py", "__init__.py"}

    async def execute(self, **kwargs) -> Response:
        scan_path_str = self.args.get("scan_path") or self.args.get("path")
        
        if not scan_path_str:
            return Response(
                message="❌ Error: 'scan_path' argument is required.\n💡 Usage: human-skills '{\"tool_name\": \"linter\", \"tool_args\": {\"scan_path\": \".\"}}'", 
                break_loop=False
            )

        linter_type = str(self.args.get("linter_type", "default")).strip().lower()
        valid_types = {"default", "rest_api"}
        if linter_type not in valid_types:
            return Response(
                message=f"❌ Error: Unknown linter_type '{linter_type}'.\n💡 Valid types: {', '.join(sorted(valid_types))}",
                break_loop=False
            )

        # --- ARGUMENT VALIDATION ---
        allowed_args = {
            "default": ["scan_path", "path", "ignored_path", "ignored_apth", "linter_type"],
            "rest_api": ["scan_path", "path", "ignored_path", "ignored_apth", "linter_type", "ignored_rules"]
        }

        valid_keys = allowed_args[linter_type]
        invalid_keys = [k for k in self.args.keys() if k not in valid_keys]
        
        if invalid_keys:
            msg = f"❌ Error: Invalid argument(s) provided: {', '.join(invalid_keys)}\n"
            msg += f"💡 Available arguments for '{linter_type}' mode: {', '.join([k for k in valid_keys if k not in ['path', 'ignored_apth']])}"
            return Response(message=msg, break_loop=False)

        scan_path = Path(scan_path_str).resolve()
        if not scan_path.exists():
            return Response(message=f"❌ Error: Path '{scan_path}' does not exist.", break_loop=False)

        custom_ignores = self.args.get("ignored_path") or self.args.get("ignored_apth") or ""
        ignored_list = {i.strip() for i in custom_ignores.split(",") if i.strip()}

        ignored_rules_raw = self.args.get("ignored_rules", "")
        ignored_rules = {r.strip() for r in ignored_rules_raw.split(",") if r.strip()}

        # ── Route to correct linter ───────────────────────────────────────────
        if linter_type == "rest_api":
            return await self.run_rest_api_audit(scan_path, ignored_list, ignored_rules)
        return await self.run_default_audit(scan_path, ignored_list)

    async def run_default_audit(self, scan_path: Path, ignored_list: set) -> Response:
        """AST-based architecture violation checker."""
        bypass_dirs = {
            "tests", ".agents", ".a0proj", ".claude", ".gemini",
            "venv", ".venv", "__pycache__", ".git", "scripts", "docs"
        }
        bypass_dirs.update(ignored_list)

        # ── Phase 1: Per-file AST violations ──────────────────────────────────
        audit_results = self.audit_project(scan_path, bypass_dirs)
        total_violations = sum(len(v) for v in audit_results.values())

        status = "✨ CLEAN ARCHITECTURE! No violations detected." if total_violations == 0 else f"🚨 Audit finished. Found {total_violations} compliance violations."

        console_msg = f"🚀 Starting human-lint [default] on: {scan_path}\n"
        console_msg += "=" * 65 + "\n"

        for file_path, violations in audit_results.items():
            console_msg += f"\n📄 {file_path}\n"
            for v in violations:
                console_msg += f"  {v}\n"

        console_msg += "=" * 65 + "\n"
        console_msg += f"{status}\n"

        if total_violations > 0 and scan_path.is_dir():
            report_path = scan_path / "REFACTORING_TASKS.md"
            self.generate_markdown_report(report_path, scan_path, audit_results)
            console_msg += f"📝 Task list generated: {report_path.name}\n"
            console_msg += "💡 Tip: Open the markdown file to track your refactoring progress.\n"

        # ── Phase 2: Project-wide import graph analysis ───────────────────────
        if scan_path.is_dir():
            graph_msg = self._analyze_import_graph(scan_path, bypass_dirs)
            if graph_msg:
                console_msg += "\n" + graph_msg

        return Response(message=console_msg, break_loop=False)

    async def run_rest_api_audit(self, scan_path: Path, ignored_list: set, ignored_rules: set) -> Response:
        """Concurrent REST API quality scorer using all analyzers in rest_api/."""
        import importlib.util
        import asyncio

        # ── Discover all analyzer modules in rest_api/ ────────────────────────
        rest_api_dir = Path(__file__).resolve().parent / "rest_api"
        if not rest_api_dir.exists():
            return Response(message="❌ Error: 'rest_api/' directory not found next to linter.py.", break_loop=False)

        analyzer_files = sorted(rest_api_dir.glob("*.py"))
        if not analyzer_files:
            return Response(message="❌ Error: No analyzer files found in rest_api/.", break_loop=False)

        # ── Load analyzer instances dynamically ───────────────────────────────
        analyzers = []
        for af in analyzer_files:
            if af.stem in ignored_rules:
                continue
            
            spec = importlib.util.spec_from_file_location(af.stem, af)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # Find the Tool subclass in the module
            for attr in vars(mod).values():
                if isinstance(attr, type) and attr.__name__ != "Tool" and hasattr(attr, "evaluate"):
                    analyzers.append((af.stem, attr()))
                    break

        # ── Collect .py files to scan ─────────────────────────────────────────
        bypass_parts = {"venv", ".venv", "__pycache__", ".git", "tests"} | ignored_list
        if scan_path.is_file():
            py_files = [scan_path]
        else:
            py_files = [
                f for f in sorted(scan_path.rglob("*.py"))
                if not any(p in bypass_parts for p in f.parts)
                and not any(part.startswith(".") for part in f.parts)
            ]

        if not py_files:
            return Response(message="ℹ️  No Python files found to score.", break_loop=False)

        # ── Two-layer router file filter ──────────────────────────────────────
        # Layer 1: directory name heuristic (fast pre-filter)
        _ROUTER_DIRS = {"routers", "routes", "api", "endpoints", "views", "handlers"}

        # Layer 2: HTTP decorator / framework content fingerprint (precise)
        import re as _re
        _HTTP_FINGERPRINT = _re.compile(
            r'(@(router|app|bp|blueprint|api)\.(get|post|put|patch|delete|head|options)\b'    # FastAPI / Flask
            r'|@(app|bp)\.route\b'                                                             # Flask @app.route
            r'|APIRouter\(\)'                                                                  # FastAPI router instance
            r'|urlpatterns\s*='                                                                # Django urls.py
            r'|path\s*\([\'\"]\s*[\w/<>]'                                                     # Django path()
            r'|Blueprint\s*\()'                                                               # Flask Blueprint
        )

        def _is_router_file(py_file: Path) -> bool:
            if py_file.name == "__init__.py":
                return False
            # Layer 1: is it in a router-ish directory?
            in_router_dir = any(p.lower() in _ROUTER_DIRS for p in py_file.parts)
            # Layer 2: does it contain HTTP handler patterns?
            try:
                snippet = py_file.read_text(encoding="utf-8", errors="ignore")[:4000]
                has_http_patterns = bool(_HTTP_FINGERPRINT.search(snippet))
            except OSError:
                return False
            return in_router_dir or has_http_patterns

        if not scan_path.is_file():
            router_files = [f for f in py_files if _is_router_file(f)]
        else:
            router_files = py_files

        if not router_files:
            return Response(
                message=(
                    f"ℹ️  No router/endpoint files detected in {scan_path.name}.\n"
                    f"   Scanned {len(py_files)} files — none matched router patterns.\n"
                    f"   💡 Router files are detected by directory name (routers/, api/, endpoints/)\n"
                    f"      or HTTP decorators (@router.get, @app.route, APIRouter, urlpatterns)."
                ),
                break_loop=False
            )

        # ── Score each router file concurrently across all analyzers ──────────
        async def score_file(py_file: Path) -> tuple[str, dict[str, tuple[float, list[str]]]]:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            if not source.strip():
                return "", {}
            try:
                import ast as _ast
                module = _ast.parse(source)
            except SyntaxError:
                module = None
            results = await asyncio.gather(
                *[asyncio.to_thread(a.evaluate, module, source) for _, a in analyzers]
            )
            return str(py_file.relative_to(scan_path if scan_path.is_dir() else scan_path.parent)), {
                name: (res[0], res[1]) if isinstance(res, tuple) else (res, []) 
                for (name, _), res in zip(analyzers, results)
            }

        file_scores = await asyncio.gather(*[score_file(f) for f in router_files])
        file_scores = [(p, s) for p, s in file_scores if p]  # drop empty

        # ── Build scorecard report ────────────────────────────────────────────
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg  = f"🚀 Starting human-lint [rest_api] on: {scan_path}\n"
        msg += "=" * 65 + "\n"
        msg += f"🔍 Detected {len(router_files)} router file(s)\n"

        overall_totals: dict[str, list[float]] = {name: [] for name, _ in analyzers}
        overall_suggestions: dict[str, set[str]] = {name: set() for name, _ in analyzers}

        for rel_path, scores_dict in file_scores:
            for name, (score, suggestions) in scores_dict.items():
                overall_totals[name].append(score)
                for sug in suggestions:
                    overall_suggestions[name].add(sug)

        # ── Project-wide averages / max ───────────────────────────────────────
        # For certain features (auth, rate limiting, caching), if they exist in ANY
        # router, the project has them. For others (naming, methods), we average.
        _USE_MAX_METRICS = {"auth_implementation", "caching_strategy", "rate_limiting", "retry_logic"}
        
        msg += "\n" + "=" * 65 + "\n"
        msg += f"📊 PROJECT API QUALITY SCORECARD\n"
        msg += "=" * 65 + "\n"
        
        project_scores = {}
        for name, vals in overall_totals.items():
            if not vals:
                final_score = 0.0
            elif name in _USE_MAX_METRICS:
                final_score = max(vals)
            else:
                final_score = sum(vals) / len(vals)
                
            project_scores[name] = final_score
            icon = "✅" if final_score >= 0.7 else ("⚠️" if final_score >= 0.4 else "❌")
            msg += f"  {icon} {name:<35} {final_score:.2f}\n"

        grand_avg = sum(project_scores.values()) / max(len(project_scores), 1)
        msg += "=" * 65 + "\n"
        msg += f"🏆 OVERALL API SCORE: {grand_avg:.2f} / 1.00  {self._score_bar(grand_avg)}\n"

        # ── Generating Suggestions for Low Scores ─────────────────────────────
        low_scores = [name for name, score in project_scores.items() if score < 0.70]
        if low_scores:
            msg += "\n💡 SUGGESTIONS FOR IMPROVEMENT:\n"
            msg += "-" * 65 + "\n"
            for name in low_scores:
                suggestions = overall_suggestions.get(name, set())
                if suggestions:
                    formatted_suggestions = "\n      ".join(f"- {s}" for s in sorted(suggestions))
                    msg += f" 🔹 {name}:\n      {formatted_suggestions}\n"
                else:
                    msg += f" 🔹 {name}:\n      - Review best practices and fix related architecture violations.\n"

        return Response(message=msg, break_loop=False)

    @staticmethod
    def _score_bar(score: float) -> str:
        filled = int(score * 10)
        return "[" + "█" * filled + "░" * (10 - filled) + "]"

    def _analyze_import_graph(self, scan_path: Path, bypass_dirs: set[str]) -> str:
        """Phase 2: Build project-wide import graph, detect circular deps, calculate coupling."""
        import re
        from collections import defaultdict

        # Collect all Python files
        py_files = [
            f for f in sorted(scan_path.rglob("*.py"))
            if not any(part in bypass_dirs for part in f.relative_to(scan_path).parts)
            and not any(part.startswith(".") for part in f.parts)
            and f.name not in self.CONFIG_INFRA_FILES
        ]

        if not py_files:
            return ""

        # ── Build module → imports graph ──────────────────────────────────────
        internal_modules: dict[str, set[str]] = defaultdict(set)

        for py_file in py_files:
            rel = py_file.relative_to(scan_path)
            module = rel.parts[0] if len(rel.parts) > 1 else "root"

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                # Extract Python imports — first component only
                for match in re.finditer(r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE):
                    imported = match.group(1).split(".")[0]
                    if imported != module:
                        internal_modules[module].add(imported)
            except Exception:
                continue

        if not internal_modules:
            return ""

        # Filter to only internal modules (both sides must exist as directories)
        all_modules = set(internal_modules.keys())
        graph: dict[str, set[str]] = defaultdict(set)

        for module, imports in internal_modules.items():
            for imp in imports:
                if imp in all_modules:
                    graph[module].add(imp)

        # ── Detect circular dependencies (DFS) ────────────────────────────────
        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycles: list[list[str]] = []

        def find_cycles(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    find_cycles(neighbor, path)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for module in all_modules:
            if module not in visited:
                find_cycles(module, [])

        # ── Calculate coupling score (0-100) ──────────────────────────────────
        total_modules = len(all_modules)
        total_connections = sum(len(deps) for deps in graph.values())
        max_connections = total_modules * (total_modules - 1) if total_modules > 1 else 1
        coupling_score = min(100, int((total_connections / max_connections) * 100))
        coupling_score = min(100, coupling_score + len(cycles) * 10)

        # ── Format output ─────────────────────────────────────────────────────
        msg = "=" * 65 + "\n"
        msg += "Import Graph Analysis\n"
        msg += "=" * 65 + "\n"
        msg += f"  Modules scanned: {total_modules}\n"
        msg += f"  Internal connections: {total_connections}\n"

        # Coupling score with visual indicator
        if coupling_score < 30:
            coupling_icon = "🟢"
            coupling_label = "Low (good)"
        elif coupling_score < 70:
            coupling_icon = "🟡"
            coupling_label = "Moderate"
        else:
            coupling_icon = "🔴"
            coupling_label = "High — consider refactoring"

        msg += f"  Coupling score: {coupling_score}/100 {coupling_icon} {coupling_label}\n"

        if cycles:
            msg += f"\n  ⚠️  Circular dependencies detected ({len(cycles)}):\n"
            for cycle in cycles:
                msg += f"    🔄 {' → '.join(cycle)}\n"
            msg += "  💡 Extract shared interfaces or create a common module to break cycles.\n"
        else:
            msg += f"\n  ✅ No circular dependencies found.\n"

        # Show module dependency map
        if graph:
            msg += f"\n  📊 Module dependency map:\n"
            for module in sorted(graph.keys()):
                deps = sorted(graph[module])
                if deps:
                    msg += f"    {module} → {', '.join(deps)}\n"

        msg += "=" * 65 + "\n"
        return msg

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
            # Only skip infra files when they are inside a 'config' directory
            in_config_dir = "config" in py_file.parts
            is_infra_file = py_file.name in self.CONFIG_INFRA_FILES and in_config_dir
            is_bypassed = is_infra_file or \
                          any(str(rel_path).startswith(d) for d in bypass_dirs) or \
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

                # Post-visit: kill switch check for main.py
                if auditor.is_main_file and auditor._has_uvicorn_run and not auditor._has_kill_pid:
                    auditor.violations.append(
                        f"L{auditor._uvicorn_run_line}: ❌ [Kill Switch Missing] 'uvicorn.run()' found without 'kill_pid(port)'. "
                        f"Add 'kill_pid(port)' before uvicorn.run() to prevent 'Address already in use' errors."
                    )

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
    # Exceptions that are project-specific business errors — raising raw built-in
    # exceptions for business logic is forbidden when helpers/exceptions.py exists.
    _RAW_EXCEPTION_TYPES = {"Exception", "ValueError", "RuntimeError", "TypeError", "KeyError"}

    def __init__(self, filename: Path, root_dir: Path, bypass_dirs: set[str]):
        self.filename = filename
        self.violations = []
        # Only exempt from pathlib rules if the file is INSIDE a 'config' directory
        _PATHLIB_EXEMPT = {"paths.py", "files.py", "logger.py", "dotenv.py", "__init__.py", "settings.py"}
        in_config_dir = "config" in filename.parts
        self.is_config_file = filename.name in _PATHLIB_EXEMPT and in_config_dir
        # settings.py is scanned for Field(default=...) silent defaults
        self.is_settings_file = filename.name == "settings.py" and in_config_dir
        # Helpers files are exempt from helpers enforcement checks
        in_helpers_dir = "helpers" in filename.parts
        self.is_helpers_file = in_helpers_dir
        # Track if file has time.sleep inside a loop (manual retry pattern)
        self._inside_loop = False
        # Kill switch tracking — main.py must call kill_pid() before uvicorn.run()
        self.is_main_file = filename.name == "main.py"
        self._has_kill_pid = False
        self._has_uvicorn_run = False
        self._uvicorn_run_line = 0

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
            
        if node.module == "os.path" and not self.is_config_file:
            os_path_blacklist = {
                "realpath": "get_abs_path",
                "exists": "exists",
                "isdir": "is_dir",
                "join": "get_abs_path or relative string concatenation"
            }
            for alias in node.names:
                if alias.name in os_path_blacklist:
                    suggestion = os_path_blacklist[alias.name]
                    self.add_violation(node, f"❌ [Config Path Violation] 'from os.path import {alias.name}' used. Use '{suggestion}' from files.py instead.")
                    
        self.generic_visit(node)

    def visit_Call(self, node):
        # 0. Kill switch tracking (main.py only)
        if self.is_main_file:
            if isinstance(node.func, ast.Name) and node.func.id == "kill_pid":
                self._has_kill_pid = True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "uvicorn":
                    self._has_uvicorn_run = True
                    self._uvicorn_run_line = node.lineno

        # 1. Print statement
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.add_violation(node, "⚠️ [Print Statement] Manual 'print()' found. Use a logger for production code.")
        
        # 2. Manual open()
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            self.add_violation(node, "❌ [Manual File I/O] Direct 'open()' call found. Use 'read_text/write_text' from config instead.")
        
        # 3. Manual os.getenv
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr in ("getenv", "getenvb"):
                self.add_violation(node, "❌ [Env Access] Direct 'os.getenv()' used. Use 'Settings' class.")
            if node.func.value.id == "os" and node.func.attr in ("open", "read", "write"):
                self.add_violation(node, f"❌ [Manual File I/O] Direct 'os.{node.func.attr}()' used. Use config utilities.")

        # 4. Keyword arguments (exist_ok=True)
        for keyword in node.keywords:
            if keyword.arg == "exist_ok" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                self.add_violation(node, "❌ [Manual Dir Creation] 'exist_ok=True' found. Use 'ensure_dir' from config instead.")
        
        # 5. Logger Compliance
        if isinstance(node.func, ast.Name) and node.func.id == "setup_logger":
            if node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                     self.add_violation(node, f"❌ [Logger Compliance] Hardcoded log filename '{arg.value}' found. Use 'Settings.LOG_DIR / \"layer.log\"'.")

        # 6. Field(default=...) silent default in settings.py
        if self.is_settings_file:
            if isinstance(node.func, ast.Name) and node.func.id == "Field":
                for kw in node.keywords:
                    if kw.arg == "default" and isinstance(kw.value, ast.Constant):
                        val = kw.value.value
                        # Only flag non-trivial defaults (not None, not empty string)
                        if val not in (None, "", "development", "production"):
                            self.add_violation(node, f"⚠️ [Silent Default] Field(default='{val}') found. Consider Field(...) to force env var requirement.")

        # 7. os.getenv with a fallback default (silent failure anywhere)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr == "getenv":
                if len(node.args) >= 2 or any(kw.arg == "default" for kw in node.keywords):
                    self.add_violation(node, "⚠️ [Silent Default] os.getenv() with fallback default found. Use Settings class — missing env vars should fail loudly.")

        # ── Helpers Enforcement ────────────────────────────────────────────────
        if not self.is_helpers_file and not self.is_config_file:

            # 8. Raw datetime.now() / datetime.utcnow() — use get_now_iso()
            if isinstance(node.func, ast.Attribute) and node.func.attr in ("now", "utcnow"):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "datetime":
                    self.add_violation(node, "⚠️ [Helpers Violation] Direct 'datetime.now()/utcnow()' used. Use 'get_now_iso()' from src.helpers instead.")

            # 9. create_async_engine() — use init_db() from helpers
            if isinstance(node.func, ast.Name) and node.func.id == "create_async_engine":
                self.add_violation(node, "❌ [Helpers Violation] Direct 'create_async_engine()' used. Use 'init_db()' from src.helpers instead.")

            # 10. time.sleep() inside a loop — manual retry pattern
            if self._inside_loop:
                if isinstance(node.func, ast.Attribute) and node.func.attr == "sleep":
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "time":
                        self.add_violation(node, "⚠️ [Helpers Violation] Manual retry pattern detected (time.sleep in loop). Use '@retry_on_failure' from src.helpers instead.")
                if isinstance(node.func, ast.Attribute) and node.func.attr == "sleep":
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "asyncio":
                        self.add_violation(node, "⚠️ [Helpers Violation] Manual async retry pattern detected (asyncio.sleep in loop). Use '@retry_async_on_failure' from src.helpers instead.")

        self.generic_visit(node)

    def visit_With(self, node):
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                call = item.context_expr
                if isinstance(call.func, ast.Name) and call.func.id == "open":
                    self.add_violation(node, "❌ [Manual File I/O] 'with open()' block found. Use 'read_text/write_text' from config instead.")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # 1. os.environ
        if isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "environ":
            self.add_violation(node, "❌ [Env Access] Direct 'os.environ' used. Use 'Settings' class.")
        
        # 2. Forbidden Path methods
        forbidden_path_methods = {
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
            "absolute": "get_abs_path"
        }
        if node.attr in forbidden_path_methods and not self.is_config_file:
            suggestion = forbidden_path_methods[node.attr]
            self.add_violation(node, f"❌ [Config Path Violation] Direct '.{node.attr}()' used. Use '{suggestion}' from src.config.files instead.")
            
        # 3. os.path methods
        os_path_blacklist = {
            "realpath": "get_abs_path",
            "exists": "exists",
            "isdir": "is_dir",
            "join": "get_abs_path or relative string concatenation"
        }
        if node.attr in os_path_blacklist and not self.is_config_file:
            is_os_path = False
            if isinstance(node.value, ast.Name) and node.value.id in ("os", "path"):
                is_os_path = True
            elif isinstance(node.value, ast.Attribute) and node.value.attr == "path":
                is_os_path = True

            if is_os_path:
                suggestion = os_path_blacklist[node.attr]
                self.add_violation(node, f"❌ [Config Path Violation] 'os.path.{node.attr}' used. Use '{suggestion}' from files.py instead.")
        
        self.generic_visit(node)

    def visit_Try(self, node):
        for handler in node.handlers:
            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                self.add_violation(handler, "❌ [Silent Exception] 'except: pass' found. Do not swallow exceptions silently.")
        self.generic_visit(node)

    def visit_Raise(self, node):
        """Detect raw raise Exception/ValueError/RuntimeError — suggest AppError hierarchy."""
        if not self.is_helpers_file and not self.is_config_file and node.exc:
            # raise ExceptionType(...) or raise ExceptionType
            exc_node = node.exc
            exc_name = None
            if isinstance(exc_node, ast.Call) and isinstance(exc_node.func, ast.Name):
                exc_name = exc_node.func.id
            elif isinstance(exc_node, ast.Name):
                exc_name = exc_node.id
            if exc_name and exc_name in self._RAW_EXCEPTION_TYPES:
                self.add_violation(node, f"⚠️ [Helpers Violation] Raw 'raise {exc_name}(...)' used. Use AppError subclasses (NotFoundError, ValidationError, etc.) from src.helpers instead.")
        self.generic_visit(node)

    # ── Loop tracking for manual retry detection ──────────────────────────────
    def visit_For(self, node):
        self._inside_loop = True
        self.generic_visit(node)
        self._inside_loop = False

    def visit_While(self, node):
        self._inside_loop = True
        self.generic_visit(node)
        self._inside_loop = False
