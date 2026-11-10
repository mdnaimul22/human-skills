import sys
import json
import asyncio
import inspect
import importlib
import importlib.util
import ast
import time
from enum import Enum
from typing import Optional, Dict, List, Any, Tuple

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from paths import (
        PROJECT_ROOT, SKILLS_DIR, STORAGE_DIR,
        HELPERS_DIR, STORAGE_BASE_DIR, EXCLUDED_NAMES,
    )
except ImportError:
    from skills.helpers.paths import (
        PROJECT_ROOT, SKILLS_DIR, STORAGE_DIR,
        HELPERS_DIR, STORAGE_BASE_DIR, EXCLUDED_NAMES,
    )

from skills.helpers.files import (
    exists, is_dir, list_files, read_text, read_json, get_rel_path,
)
from skills.helpers.tool import ToolStatus, Response


class DispatchPhase(str, Enum):
    INGESTED = "ingested"
    VALIDATING = "validating"
    RESOLVING = "resolving"
    EXECUTING = "executing"
    FORMATTING = "formatting"
    COMPLETED = "completed"
    FAILED = "failed"


class DispatchResult:
    def __init__(
        self, status: str, phase: DispatchPhase, message: str,
        tool_name: str = "", duration_ms: float = 0.0,
        data: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = None, hint: Optional[str] = None,
    ) -> None:
        self.status = status
        self.phase = phase
        self.message = message
        self.tool_name = tool_name
        self.duration_ms = duration_ms
        self.data = data or {}
        self.error_code = error_code
        self.hint = hint

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "status": self.status,
            "phase": self.phase.value if isinstance(self.phase, DispatchPhase) else str(self.phase),
            "tool_name": self.tool_name,
            "duration_ms": round(self.duration_ms, 2),
            "message": self.message,
            "data": self.data,
        }
        if self.error_code:
            res["error_code"] = self.error_code
        if self.hint:
            res["hint"] = self.hint
        return res


_REGISTRY_CACHE: Dict[str, dict] = {}
_REGISTRY_CACHE_TIME: float = 0.0
_REGISTRY_TTL_SECONDS: float = 60.0


def _extract_message(result: Any) -> str:
    try:
        return str(result.message)
    except AttributeError:
        return str(result)


def _extract_success(result: Any) -> bool:
    try:
        return bool(result.success)
    except AttributeError:
        return True


def _get_category_for_path(path: str) -> str:
    try:
        storage_rel = get_rel_path(path, base=STORAGE_BASE_DIR)
        parts = storage_rel.replace("\\", "/").split("/")
        return parts[0] if len(parts) > 1 else "general"
    except Exception:
        return "other"


def _resolve_runner(module_name: str, path: str) -> Optional[dict]:
    try:
        content = read_text(path)
        tree = ast.parse(content, filename=path)
        has_tool = any(
            isinstance(node, ast.ClassDef)
            and any(isinstance(base, ast.Name) and base.id == "Tool" for base in node.bases)
            for node in tree.body
        )
        if not has_tool:
            return None
    except Exception as exc:
        _warn(f"Failed to parse AST for '{module_name}': {exc}")

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        _warn(f"Failed to load '{module_name}': {exc}")
        return None

    target_cls = None
    for name, obj in inspect.getmembers(module, inspect.isclass):
        base_names = [base.__name__ for base in getattr(obj, "__bases__", [])]
        if "Tool" in base_names and name != "Tool":
            target_cls = obj
            break

    if target_cls is not None:
        execute_method = getattr(target_cls, "execute", None)
        if callable(execute_method):
            def _run_async(args: dict, _cls=target_cls) -> Response:
                t0 = time.perf_counter()
                try:
                    instance = _cls(args=args)
                    raw_res = asyncio.run(instance.execute())
                    duration = (time.perf_counter() - t0) * 1000.0
                    if isinstance(raw_res, Response):
                        raw_res.duration_ms = duration
                        return raw_res
                    msg = _extract_message(raw_res)
                    succ = _extract_success(raw_res)
                    return Response(
                        message=msg, success=succ, duration_ms=duration,
                        status=ToolStatus.SUCCESS if succ else ToolStatus.EXECUTION_ERROR,
                    )
                except Exception as exc:
                    duration = (time.perf_counter() - t0) * 1000.0
                    return Response(
                        message=f"❌ Unhandled tool exception: {exc}", success=False,
                        status=ToolStatus.CRASHED, duration_ms=duration, error_code="UNHANDLED_EXCEPTION",
                    )

            return {
                "runner": _run_async,
                "name": getattr(target_cls, "name", module_name) or module_name,
                "description": getattr(target_cls, "description", ""),
                "arguments": getattr(target_cls, "arguments", ""),
                "instruction": getattr(target_cls, "instruction", ""),
                "category": _get_category_for_path(path),
                "file_path": path,
            }
    return None


def _build_registry(force_refresh: bool = False) -> Dict[str, dict]:
    global _REGISTRY_CACHE, _REGISTRY_CACHE_TIME
    now = time.time()
    if not force_refresh and _REGISTRY_CACHE and (now - _REGISTRY_CACHE_TIME < _REGISTRY_TTL_SECONDS):
        return _REGISTRY_CACHE

    registry: Dict[str, dict] = {}
    py_files: list[Any] = []
    if exists(STORAGE_DIR):
        py_files.extend(list_files(STORAGE_DIR, "**/scripts/*.py"))
    py_files.extend(list_files(SKILLS_DIR, "*/scripts/*.py"))

    for py_file in sorted(set(py_files)):
        if py_file.name in EXCLUDED_NAMES:
            continue
        parent_dir = str(py_file.parent)
        grandparent_dir = str(py_file.parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        if grandparent_dir not in sys.path:
            sys.path.insert(0, grandparent_dir)

        tool_name = py_file.stem
        runner = _resolve_runner(tool_name, str(py_file))
        if runner is not None:
            registry[tool_name] = runner
            cls_name = runner.get("name")
            if cls_name and cls_name != tool_name and cls_name not in registry:
                registry[cls_name] = runner

    _REGISTRY_CACHE = registry
    _REGISTRY_CACHE_TIME = now
    return _REGISTRY_CACHE


def _get_categories_map() -> Dict[str, List[str]]:
    categories: Dict[str, List[str]] = {}
    if exists(STORAGE_DIR):
        for md in sorted(list_files(STORAGE_DIR, "**/SKILL.md")):
            rel = get_rel_path(str(md.parent), base=STORAGE_BASE_DIR)
            parts = rel.replace("\\", "/").split("/")
            cat = parts[0] if len(parts) > 1 else "general"
            categories.setdefault(cat, []).append(md.parent.name)

    for path in sorted(list_files(SKILLS_DIR, "*")):
        path_str = str(path)
        if is_dir(path_str) and path.name not in ("helpers", "storage") and exists(f"{path_str}/SKILL.md"):
            categories.setdefault("other", []).append(path.name)
    return categories


def _build_category_index(categories_map: Dict[str, List[str]]) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for real_name in categories_map.keys():
        lowered = real_name.lower()
        index[lowered] = real_name
        index[lowered.replace(" ", "_")] = real_name
        index[lowered.replace(" ", "-")] = real_name
        index[lowered.replace("_", "-")] = real_name
        index[lowered.replace("-", "_")] = real_name
        stripped = lowered.replace(" ", "").replace("_", "").replace("-", "")
        index[stripped] = real_name
    return index


def _match_category(target: str, categories_map: Dict[str, List[str]]) -> Optional[str]:
    query = target.strip().lower()
    if not query:
        return None
    index = _build_category_index(categories_map)
    if query in index:
        return index[query]
    query_norm = query.replace(" ", "").replace("_", "").replace("-", "")
    if query_norm in index:
        return index[query_norm]
    matches = {real_name for k, real_name in index.items() if query_norm in k}
    if len(matches) == 1:
        return next(iter(matches))
    return None


def _find_skill_md(skill_name: str) -> Optional[str]:
    clean_name = skill_name.strip()
    clean_lower = clean_name.lower().replace("_", "-")

    if clean_lower in ("human-skills", "human_skills", "dispatcher", "main", "root"):
        for root_md in (
            ".agents/skills/human-skills/SKILL.md",
            f"{HELPERS_DIR}/SKILL.md",
            f"{SKILLS_DIR}/SKILL.md",
        ):
            if exists(root_md):
                return root_md

    if exists(STORAGE_DIR):
        direct = f"{STORAGE_DIR}/{clean_name}/SKILL.md"
        if exists(direct):
            return direct
        for md_path in list_files(STORAGE_DIR, "**/SKILL.md"):
            if md_path.parent.name.lower().replace("_", "-") == clean_lower:
                return str(md_path)

    direct_root = f"{SKILLS_DIR}/{clean_name}/SKILL.md"
    if exists(direct_root):
        return direct_root

    for path in list_files(SKILLS_DIR, "*"):
        path_str = str(path)
        if is_dir(path_str) and path.name.lower().replace("_", "-") == clean_lower:
            candidate = f"{path_str}/SKILL.md"
            if exists(candidate):
                return candidate
    return None


def _warn(msg: str) -> None:
    print(f"[execute] WARNING: {msg}", file=sys.stderr)


def _read_stdin_text() -> str:
    try:
        if sys.stdin.isatty():
            return ""
    except Exception:
        pass
    try:
        data = sys.stdin.read()
    except Exception:
        return ""
    return data or ""


def _coerce_arg_value(raw: str):
    text = raw.strip()
    if text == "":
        return ""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return raw


def _parse_tool_style(argv: List[str]) -> dict:
    tool_name = ""
    tool_args: Dict[str, object] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("--tool", "--tool_name", "--tool-name") and not tool_name:
            i += 1
            if i >= len(argv):
                raise ValueError("--tool requires a tool name.")
            token = argv[i]
            if "=" in token and not tool_name:
                _, _, val = token.partition("=")
                tool_name = val.strip()
            else:
                tool_name = token.strip()
        elif tok.startswith("--tool=") or tok.startswith("--tool_name=") or tok.startswith("--tool-name="):
            _, _, val = tok.partition("=")
            tool_name = val.strip()
        elif tok in ("--arg", "--args", "-a"):
            i += 1
            if i >= len(argv):
                raise ValueError("--arg requires k=v.")
            kv = argv[i]
            key, sep, val = kv.partition("=")
            if not sep or not key.strip():
                raise ValueError(f"Bad --arg {kv!r}: expected k=v.")
            tool_args[key.strip()] = _coerce_arg_value(val)
        elif tok.startswith("--arg=") or tok.startswith("--args="):
            _, _, kv = tok.partition("=")
            key, sep, val = kv.partition("=")
            if not sep or not key.strip():
                raise ValueError(f"Bad {tok!r}: expected --arg k=v.")
            tool_args[key.strip()] = _coerce_arg_value(val)
        else:
            raise ValueError(f"Unexpected argument {tok!r} in --tool mode.")
        i += 1
    if not tool_name:
        raise ValueError("--tool requires a tool name.")
    return {"tool_name": tool_name, "tool_args": tool_args}


def _load_payload(source: str) -> dict:
    stripped = source.strip()
    if not stripped:
        raise ValueError("Empty payload.")
    if stripped.endswith(".json") and exists(stripped):
        return read_json(stripped)
    if len(stripped) >= 2 and stripped[0] == "'" and stripped[-1] == "'":
        inner = stripped[1:-1].strip()
        if inner.startswith("{"):
            stripped = inner
    return json.loads(stripped)


def _print_usage() -> None:
    print(__doc__ or "human-skills Command Center")
    print("\nUsage:")
    print("  • human-skills --list [all | <dir_name>] (or --list-all)")
    print("  • human-skills --skill_info <skill_name>")
    print("  • human-skills --tool_info <tool_name>")
    print("  • human-skills '{\"tool_name\": \"<name>\", \"tool_args\": {...}}'")
    print("  • human-skills --json '{\"tool_name\": \"<name>\", \"tool_args\": {...}}'  (machine-readable JSON)")
    print("  • human-skills payload.json  (file path, Windows-safe)")
    print("  • echo {\"tool_name\": ...} | human-skills  (stdin, Windows-safe)")
    print("  • human-skills --tool <name> --arg k=v [--arg k2=v2 ...]  (no JSON quoting)")


def _is_json_requested(payload: dict) -> bool:
    if payload.get("output_format") == "json" or payload.get("json") is True:
        return True
    args = payload.get("tool_args")
    if isinstance(args, dict):
        return args.get("output_format") == "json" or args.get("json") is True
    return False


def dispatch_structured(payload: dict) -> DispatchResult:
    tool_name = str(payload.get("tool_name", "")).strip()
    tool_args = payload.get("tool_args", {})

    if not tool_name:
        return DispatchResult(
            status=ToolStatus.VALIDATION_ERROR.value, phase=DispatchPhase.VALIDATING,
            message="Error: `tool_name` is required in the JSON payload.",
            error_code="MISSING_TOOL_NAME", hint="Provide a valid tool_name in your payload.",
        )

    if not isinstance(tool_args, dict):
        return DispatchResult(
            status=ToolStatus.VALIDATION_ERROR.value, phase=DispatchPhase.VALIDATING,
            message="Error: `tool_args` must be a JSON object (dict).",
            tool_name=tool_name, error_code="INVALID_TOOL_ARGS",
            hint="tool_args must be a dictionary of arguments.",
        )

    registry = _build_registry()
    tool_index = {name.lower(): name for name in registry.keys()}
    for name in list(registry.keys()):
        tool_index[name.lower().replace("-", "_")] = name
        tool_index[name.lower().replace("_", "-")] = name

    target_tool = tool_index.get(tool_name.lower())
    if not target_tool:
        target_tool = tool_index.get(tool_name.lower().replace("-", "_"))

    if not target_tool or target_tool not in registry:
        available = ", ".join(sorted(registry.keys())) or "(none)"
        return DispatchResult(
            status=ToolStatus.NOT_FOUND.value, phase=DispatchPhase.RESOLVING,
            message=f"Error: Unknown tool '{tool_name}'. Available tools: {available}",
            tool_name=tool_name, error_code="UNKNOWN_TOOL",
            hint="Check available tools with: human-skills --list all",
        )

    runner_meta = registry[target_tool]
    normalised = dict(tool_args)

    try:
        raw_res = runner_meta["runner"](normalised)
        if isinstance(raw_res, Response):
            res_obj = raw_res
        elif isinstance(raw_res, tuple) and len(raw_res) >= 2:
            res_obj = Response(
                message=str(raw_res[0]), success=bool(raw_res[1]),
                status=ToolStatus.SUCCESS if raw_res[1] else ToolStatus.EXECUTION_ERROR,
            )
        else:
            res_obj = Response(message=str(raw_res), success=True, status=ToolStatus.SUCCESS)
    except Exception as exc:
        res_obj = Response(
            message=f"Error: Tool execution raised exception: {exc}",
            success=False, status=ToolStatus.CRASHED, error_code="EXECUTION_CRASH",
        )

    status_str = res_obj.status.value if isinstance(res_obj.status, ToolStatus) else ("success" if res_obj.success else "execution_error")
    phase = DispatchPhase.COMPLETED if res_obj.success else DispatchPhase.FAILED

    return DispatchResult(
        status=status_str, phase=phase, message=res_obj.message,
        tool_name=target_tool, duration_ms=res_obj.duration_ms,
        data=res_obj.additional or {}, error_code=res_obj.error_code,
    )


def dispatch_with_status(payload: dict) -> tuple[str, bool]:
    is_json = _is_json_requested(payload)
    result = dispatch_structured(payload)
    is_success = (result.status == ToolStatus.SUCCESS.value)
    if is_json:
        return json.dumps(result.to_dict(), indent=2), is_success
    return result.message, is_success


def dispatch(payload: dict) -> str:
    return dispatch_with_status(payload)[0]


def _handle_list(args: List[str]) -> None:
    registry = _build_registry()
    categories = _get_categories_map()
    all_categories = sorted(categories.keys())

    if not args or (len(args) == 1 and args[0].strip().lower() == "all"):
        total_skills = sum(len(v) for v in categories.values())
        print("=" * 70)
        print(f"🎯 HUMAN SKILLS COMMAND CENTER — ALL SKILLS ({total_skills} total across {len(categories)} categories)")
        print("=" * 70)

        for cat in all_categories:
            skills = sorted(categories[cat])
            cat_tools = sorted([t_name for t_name, t_info in registry.items() if t_info.get("category") == cat])
            tools_badge = f", {len(cat_tools)} tools" if cat_tools else ""
            print(f"\n  📁 [{cat}] ({len(skills)} skills{tools_badge})")
            for skill in skills:
                print(f"     • {skill}")

        print("\n" + "-" * 70)
        if not registry:
            print("🛠️ Discovered Tools: None")
        else:
            print(f"🛠️ Discovered Tools ({len(registry)} total):")
            for name, info in sorted(registry.items()):
                cat_label = f" ({info.get('category', 'custom')})" if info.get("category") else ""
                print(f"  • {name}{cat_label}")

        print("\n💡 Quick Navigation:")
        print("  • List specific category: human-skills --list <dir_name>  (e.g. human-skills --list custom)")
        print("  • Read skill instructions: human-skills --skill_info <skill_name>")
        print("  • Inspect tool metadata:   human-skills --tool_info <tool_name>")
        print("=" * 70)
        sys.exit(0)

    target_query = args[0].strip()

    if "," in target_query and all(f.strip().lower() in ("name", "description", "arguments", "instruction", "category") for f in target_query.split(",")):
        fields = [f.strip().lower() for f in target_query.split(",")]
        output = {}
        for tool_id, tool_info in registry.items():
            tool_data = {f: tool_info.get(f, "") for f in fields}
            output[tool_id] = tool_data
        print(json.dumps(output, indent=2))
        sys.exit(0)

    matched_cat = _match_category(target_query, categories)

    if matched_cat is not None:
        skills = sorted(categories.get(matched_cat, []))
        cat_tools = sorted([t_name for t_name, t_info in registry.items() if t_info.get("category") == matched_cat])

        print("=" * 70)
        print(f"📁 STORAGE CATEGORY: [{matched_cat}] ({len(skills)} skills, {len(cat_tools)} tools)")
        print("=" * 70)

        print("\n📜 Skills:")
        if skills:
            for skill in skills:
                print(f"  • {skill}")
        else:
            print("  (No skills found in this category)")

        print(f"\n🛠️ Tools in [{matched_cat}]:")
        if cat_tools:
            for t in cat_tools:
                t_desc = registry[t].get("description", "")
                t_desc_short = f" — {t_desc[:60]}..." if len(t_desc) > 60 else (f" — {t_desc}" if t_desc else "")
                print(f"  • {t}{t_desc_short}")
        else:
            print("  (No standalone tools discovered in this category)")

        print("\n" + "-" * 70)
        print("💡 Quick Navigation:")
        print("  • Read skill documentation: human-skills --skill_info <skill_name>")
        print("  • Inspect tool parameters:  human-skills --tool_info <tool_name>")
        print("  • View all categories:      human-skills --list all")
        print("=" * 70)
        sys.exit(0)

    print(f"❌ Error: Category/Directory '{target_query}' not found in storage.\n", file=sys.stderr)
    print("Please use a correct directory name. Available storage categories:", file=sys.stderr)
    for cat in all_categories:
        count = len(categories[cat])
        print(f"  📁 {cat} ({count} skills)", file=sys.stderr)

    print("\n💡 Usage:", file=sys.stderr)
    print("  • List specific category: human-skills --list <dir_name>  (e.g. human-skills --list custom)", file=sys.stderr)
    print("  • List all categories:      human-skills --list all", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    wants_json = False
    if "--json" in sys.argv:
        sys.argv.remove("--json")
        wants_json = True

    if len(sys.argv) < 2:
        stdin_text = _read_stdin_text()
        if stdin_text.strip():
            try:
                payload = _load_payload(stdin_text)
            except (json.JSONDecodeError, ValueError) as e:
                err_msg = f"Error: Invalid JSON on stdin — {e}"
                if wants_json:
                    print(json.dumps({"status": "validation_error", "phase": "ingested", "message": err_msg}, indent=2))
                else:
                    print(err_msg, file=sys.stderr)
                    print("Hint: pipe valid JSON, pass a payload.json file, or use --tool NAME --arg k=v.", file=sys.stderr)
                sys.exit(1)
            if wants_json:
                payload["output_format"] = "json"
            message, ok = dispatch_with_status(payload)
            print(message)
            sys.exit(0 if ok else 1)
        _print_usage()
        sys.exit(0)

    if sys.argv[1] in ("-h", "--help"):
        _print_usage()
        sys.exit(0)

    if sys.argv[1] == "--skill_info":
        if len(sys.argv) < 3:
            print("Error: --skill_info requires a skill name.", file=sys.stderr)
            sys.exit(1)
        skill_name = sys.argv[2]
        skill_md_path = _find_skill_md(skill_name)
        if not skill_md_path or not exists(skill_md_path):
            print(f"Error: Skill documentation for '{skill_name}' not found.", file=sys.stderr)
            sys.exit(1)
        print(read_text(skill_md_path))
        sys.exit(0)

    if sys.argv[1] == "--tool_info":
        if len(sys.argv) < 3:
            print("Error: --tool_info requires an exact tool name.", file=sys.stderr)
            sys.exit(1)
        target_tool = sys.argv[2]
        registry = _build_registry()
        tool_index = {name.lower(): name for name in registry.keys()}
        for name in list(registry.keys()):
            tool_index[name.lower().replace("-", "_")] = name
            tool_index[name.lower().replace("_", "-")] = name

        actual_tool = tool_index.get(target_tool.lower())
        if not actual_tool:
            actual_tool = tool_index.get(target_tool.lower().replace("-", "_"))

        if not actual_tool or actual_tool not in registry:
            print(f"Error: Tool '{target_tool}' not found.", file=sys.stderr)
            sys.exit(1)

        tool_info = registry[actual_tool]
        output = {
            "name": tool_info.get("name", actual_tool),
            "description": tool_info.get("description", ""),
            "arguments": tool_info.get("arguments", ""),
            "instruction": tool_info.get("instruction", ""),
            "category": tool_info.get("category", ""),
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    if sys.argv[1] in ("--list", "--list-all", "--list_all", "--list all"):
        list_args = ["all"] if sys.argv[1] in ("--list-all", "--list_all", "--list all") else sys.argv[2:]
        _handle_list(list_args)

    if sys.argv[1] in ("--tool", "--tool_name", "--tool-name") or sys.argv[1].startswith("--tool"):
        try:
            payload = _parse_tool_style(sys.argv[1:])
        except ValueError as e:
            err_msg = f"Error: {e}"
            if wants_json:
                print(json.dumps({"status": "validation_error", "phase": "ingested", "message": err_msg}, indent=2))
            else:
                print(err_msg, file=sys.stderr)
                print("Usage: human-skills --tool <name> --arg k=v [--arg k2=v2 ...]", file=sys.stderr)
            sys.exit(1)
        if wants_json:
            payload["output_format"] = "json"
        message, ok = dispatch_with_status(payload)
        print(message)
        sys.exit(0 if ok else 1)

    if sys.argv[1] in ("-", "--stdin"):
        stdin_text = _read_stdin_text()
        if not stdin_text.strip():
            print("Error: No JSON received on stdin.", file=sys.stderr)
            sys.exit(1)
        try:
            payload = _load_payload(stdin_text)
        except (json.JSONDecodeError, ValueError) as e:
            err_msg = f"Error: Invalid JSON on stdin — {e}"
            if wants_json:
                print(json.dumps({"status": "validation_error", "phase": "ingested", "message": err_msg}, indent=2))
            else:
                print(err_msg, file=sys.stderr)
            sys.exit(1)
        if wants_json:
            payload["output_format"] = "json"
        message, ok = dispatch_with_status(payload)
        print(message)
        sys.exit(0 if ok else 1)

    source = " ".join(sys.argv[1:])
    try:
        payload = _load_payload(source)
    except (json.JSONDecodeError, ValueError) as e:
        err_msg = f"Error: Invalid JSON — {e}"
        if wants_json:
            print(json.dumps({"status": "validation_error", "phase": "ingested", "message": err_msg}, indent=2))
        else:
            print(err_msg, file=sys.stderr)
            print("Windows-safe alternatives (no quoting needed):", file=sys.stderr)
            print("  human-skills payload.json", file=sys.stderr)
            print("  echo JSON | human-skills  (stdin, no quoting needed)", file=sys.stderr)
            print("  human-skills --tool <name> --arg k=v", file=sys.stderr)
        sys.exit(1)

    if wants_json:
        payload["output_format"] = "json"
    message, ok = dispatch_with_status(payload)
    print(message)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
