import ast
import asyncio
import importlib.util
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from helpers.tool import Tool, Response


class Linter(Tool):
    name: str = "linter"
    description: str = "Scans Python projects for architecture violations and strict type safety (Any/getattr). Supports multiple linter types: 'default' (AST-based audit) and 'rest_api' (REST API quality scoring)."
    arguments: dict = {
        "scan_path": "Path to the project directory or a specific .py file to audit (REQUIRED).",
        "linter_type": "Linter mode: 'default' (architecture violations & strict type safety) or 'rest_api' (API quality score). Defaults to 'default'.",
        "ignored_path": "Comma-separated list of directory names to skip during scanning.",
        "ignored_rules": "Comma-separated list of analyzer or rule names to skip (e.g. 'type_safety,kill_switch' in default mode, or 'auth,rate_limiting' in rest_api mode)."
    }
    instruction: str = "Audit your codebase. Use linter_type='default' for architecture violations & type safety, 'rest_api' for REST API quality scoring."

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

        allowed_args = {
            "default": ["scan_path", "path", "ignored_path", "ignored_apth", "linter_type", "ignored_rules"],
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

        if linter_type == "rest_api":
            return await self.run_rest_api_audit(scan_path, ignored_list, ignored_rules)
        return await self.run_default_audit(scan_path, ignored_list, ignored_rules)

    def _load_default_rules(self, ignored_rules: set[str]) -> list[tuple[str, type]]:
        default_dir = Path(__file__).resolve().parent / "default"
        if not default_dir.exists():
            return []
        sys_path_dir = str(Path(__file__).resolve().parent)
        if sys_path_dir not in sys.path:
            sys.path.insert(0, sys_path_dir)
        from default.base import BaseRule
        rule_files = sorted(default_dir.glob("*.py"))
        rules = []
        for rf in rule_files:
            if rf.name == "base.py" or rf.name.startswith("_") or rf.stem in ignored_rules:
                continue
            spec = importlib.util.spec_from_file_location(f"default.{rf.stem}", rf)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[f"default.{rf.stem}"] = mod
            spec.loader.exec_module(mod)
            for attr in vars(mod).values():
                if isinstance(attr, type) and issubclass(attr, BaseRule) and attr is not BaseRule:
                    rules.append((rf.stem, attr))
                    break
        return rules

    def audit_project(self, target_path: Path, bypass_dirs: set[str], ignored_rules: set[str]) -> tuple[dict, list[str]]:
        if target_path.is_file():
            py_files = [target_path]
            root_dir = target_path.parent
        else:
            py_files = list(target_path.rglob("*.py"))
            root_dir = target_path

        rule_classes = self._load_default_rules(ignored_rules)
        sys_path_dir = str(Path(__file__).resolve().parent)
        if sys_path_dir not in sys.path:
            sys.path.insert(0, sys_path_dir)
        from default.base import FileContext

        results = {}
        advisories = []

        for py_file in sorted(py_files):
            rel_path = py_file.relative_to(root_dir)
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

                ctx = FileContext(py_file, root_dir, bypass_dirs, content)
                file_violations = []

                for _, rule_cls in rule_classes:
                    rule = rule_cls(ctx)
                    v, a = rule.run(tree)
                    file_violations.extend(v)
                    advisories.extend(a)

                if file_violations:
                    file_violations.sort(
                        key=lambda v: int(v.split(":")[0][1:])
                        if v.startswith("L") and ":" in v and v.split(":")[0][1:].isdigit()
                        else 999999
                    )
                    results[str(rel_path)] = file_violations
            except Exception as e:
                results[str(rel_path)] = [f"⚠️ Error parsing file: {e}"]

        return results, list(dict.fromkeys(advisories))

    async def run_default_audit(self, scan_path: Path, ignored_list: set, ignored_rules: set) -> Response:
        bypass_dirs = {
            "tests", ".agents", ".a0proj", ".claude", ".gemini",
            "venv", ".venv", "__pycache__", ".git", "scripts", "docs"
        }
        bypass_dirs.update(ignored_list)

        audit_results, advisories = self.audit_project(scan_path, bypass_dirs, ignored_rules)
        total_violations = sum(len(v) for v in audit_results.values())

        status = "✨ CLEAN ARCHITECTURE! No violations detected." if total_violations == 0 else f"🚨 Audit finished. Found {total_violations} compliance violations."

        console_msg = f"🚀 Starting human-lint [default] on: {scan_path}\n"
        console_msg += "=" * 65 + "\n"

        for file_path, violations in audit_results.items():
            console_msg += f"\n📄 {file_path}\n"
            for v in violations:
                console_msg += f"  {v}\n"

        has_type_safety = any(
            any("[Type Safety Violation]" in v for v in file_violations)
            for file_violations in audit_results.values()
        )
        if has_type_safety:
            advisories.append(
                "⚠️ [Type Safety Advisory] Defensive probing ('hasattr', 'getattr', 'setattr'), type branching/tautology ('isinstance'), or untyped 'Any'/'object' detected. "
                "Define explicit Pydantic schemas, TypedDict, or Protocols, and use direct attribute access (.attr)."
            )

        if advisories:
            console_msg += "\n" + "-" * 65 + "\n"
            console_msg += "💡 Architecture Advisories & Warnings:\n"
            for adv in advisories:
                console_msg += f"  {adv}\n"

        console_msg += "=" * 65 + "\n"
        console_msg += f"{status}\n"

        if total_violations > 0 and scan_path.is_dir():
            report_path = scan_path / "REFACTORING_TASKS.md"
            self.generate_markdown_report(report_path, scan_path, audit_results, advisories)
            console_msg += f"📝 Task list generated: {report_path.name}\n"
            console_msg += "💡 Tip: Open the markdown file to track your refactoring progress.\n"

        if scan_path.is_dir():
            graph_msg = self._analyze_import_graph(scan_path, bypass_dirs)
            if graph_msg:
                console_msg += "\n" + graph_msg

        return Response(message=console_msg, break_loop=False)

    def generate_markdown_report(self, report_path: Path, root_dir: Path, results: dict, advisories: list[str] = None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = [
            f"# 🏗️ Refactoring Tasks: {root_dir.name}",
            f"> Generated by **human-skills** on {now}",
            "\n## Summary",
            f"- **Project Directory:** `{root_dir}`",
            f"- **Total Violations:** {sum(len(v) for v in results.values())}",
            f"- **Files to Refactor:** {len(results)}",
        ]
        if advisories:
            content.append("\n### 💡 Architecture Guidance & Advisories")
            for adv in advisories:
                content.append(f"> {adv}")
        content.append("\n---\n")

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
                    task = v.replace("❌ ", "").replace("⚠️ ", "")
                    lines = task.split("\n")
                    content.append(f"- [ ] {lines[0]}")
                    for sub in lines[1:]:
                        content.append(f"  {sub.strip()}")
            content.append("")

        report_path.write_text("\n".join(content), encoding="utf-8")

    async def run_rest_api_audit(self, scan_path: Path, ignored_list: set, ignored_rules: set) -> Response:
        rest_api_dir = Path(__file__).resolve().parent / "rest_api"
        if not rest_api_dir.exists():
            return Response(message="❌ Error: 'rest_api/' directory not found next to linter.py.", break_loop=False)

        analyzer_files = sorted(rest_api_dir.glob("*.py"))
        if not analyzer_files:
            return Response(message="❌ Error: No analyzer files found in rest_api/.", break_loop=False)

        analyzers = []
        for af in analyzer_files:
            if af.stem in ignored_rules:
                continue

            spec = importlib.util.spec_from_file_location(af.stem, af)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for attr in vars(mod).values():
                if isinstance(attr, type) and attr.__name__ != "Tool" and hasattr(attr, "evaluate"):
                    analyzers.append((af.stem, attr()))
                    break

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

        router_dirs = {"routers", "routes", "api", "endpoints", "views", "handlers"}
        http_fingerprint = re.compile(
            r'(@(router|app|bp|blueprint|api)\.(get|post|put|patch|delete|head|options)\b'
            r'|@(app|bp)\.route\b'
            r'|APIRouter\(\)'
            r'|urlpatterns\s*='
            r'|path\s*\([\'\"]\s*[\w/<>]'
            r'|Blueprint\s*\()'
        )

        def is_router_file(py_file: Path) -> bool:
            if py_file.name == "__init__.py":
                return False
            in_router_dir = any(p.lower() in router_dirs for p in py_file.parts)
            try:
                snippet = py_file.read_text(encoding="utf-8", errors="ignore")[:4000]
                has_http_patterns = bool(http_fingerprint.search(snippet))
            except OSError:
                return False
            return in_router_dir or has_http_patterns

        if not scan_path.is_file():
            router_files = [f for f in py_files if is_router_file(f)]
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

        async def score_file(py_file: Path) -> tuple[str, dict[str, tuple[float, list[str]]]]:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            if not source.strip():
                return "", {}
            try:
                module = ast.parse(source)
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
        file_scores = [(p, s) for p, s in file_scores if p]

        msg = f"🚀 Starting human-lint [rest_api] on: {scan_path}\n"
        msg += "=" * 65 + "\n"
        msg += f"🔍 Detected {len(router_files)} router file(s)\n"

        overall_totals: dict[str, list[float]] = {name: [] for name, _ in analyzers}
        overall_suggestions: dict[str, set[str]] = {name: set() for name, _ in analyzers}

        for rel_path, scores_dict in file_scores:
            for name, (score, suggestions) in scores_dict.items():
                overall_totals[name].append(score)
                for sug in suggestions:
                    overall_suggestions[name].add(sug)

        use_max_metrics = {"auth_implementation", "caching_strategy", "rate_limiting", "retry_logic"}

        msg += "\n" + "=" * 65 + "\n"
        msg += "📊 PROJECT API QUALITY SCORECARD\n"
        msg += "=" * 65 + "\n"

        project_scores = {}
        for name, vals in overall_totals.items():
            if not vals:
                final_score = 0.0
            elif name in use_max_metrics:
                final_score = max(vals)
            else:
                final_score = sum(vals) / len(vals)

            project_scores[name] = final_score
            icon = "✅" if final_score >= 0.7 else ("⚠️" if final_score >= 0.4 else "❌")
            msg += f"  {icon} {name:<35} {final_score:.2f}\n"

        grand_avg = sum(project_scores.values()) / max(len(project_scores), 1)
        msg += "=" * 65 + "\n"
        msg += f"🏆 OVERALL API SCORE: {grand_avg:.2f} / 1.00  {self._score_bar(grand_avg)}\n"

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
        py_files = [
            f for f in sorted(scan_path.rglob("*.py"))
            if not any(part in bypass_dirs for part in f.relative_to(scan_path).parts)
            and not any(part.startswith(".") for part in f.parts)
            and f.name not in self.CONFIG_INFRA_FILES
        ]

        if not py_files:
            return ""

        internal_modules: dict[str, set[str]] = defaultdict(set)

        for py_file in py_files:
            rel = py_file.relative_to(scan_path)
            module = rel.parts[0] if len(rel.parts) > 1 else "root"

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for match in re.finditer(r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE):
                    imported = match.group(1).split(".")[0]
                    if imported != module:
                        internal_modules[module].add(imported)
            except Exception:
                continue

        if not internal_modules:
            return ""

        all_modules = set(internal_modules.keys())
        graph: dict[str, set[str]] = defaultdict(set)

        for module, imports in internal_modules.items():
            for imp in imports:
                if imp in all_modules:
                    graph[module].add(imp)

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

        total_modules = len(all_modules)
        total_connections = sum(len(deps) for deps in graph.values())
        max_connections = total_modules * (total_modules - 1) if total_modules > 1 else 1
        coupling_score = min(100, int((total_connections / max_connections) * 100))
        coupling_score = min(100, coupling_score + len(cycles) * 10)

        msg = "=" * 65 + "\n"
        msg += "Import Graph Analysis\n"
        msg += "=" * 65 + "\n"
        msg += f"  Modules scanned: {total_modules}\n"
        msg += f"  Internal connections: {total_connections}\n"

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

        if graph:
            msg += f"\n  📊 Module dependency map:\n"
            for module in sorted(graph.keys()):
                deps = sorted(graph[module])
                if deps:
                    msg += f"    {module} → {', '.join(deps)}\n"

        msg += "=" * 65 + "\n"
        return msg
