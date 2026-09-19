import sys
import json
import asyncio
import inspect
import importlib
import importlib.util
import ast
from typing import Optional, Dict, List

try:
    from skills.helpers.paths import (
        PROJECT_ROOT,
        SKILLS_DIR,
        STORAGE_DIR,
        HELPERS_DIR,
        STORAGE_BASE_DIR,
        EXCLUDED_NAMES,
    )
    from skills.helpers.files import (
        exists,
        is_dir,
        list_files,
        read_text,
        read_json,
        get_rel_path,
    )
except ImportError:
    from paths import (
        PROJECT_ROOT,
        SKILLS_DIR,
        STORAGE_DIR,
        HELPERS_DIR,
        STORAGE_BASE_DIR,
        EXCLUDED_NAMES,
    )
    from files import (
        exists,
        is_dir,
        list_files,
        read_text,
        read_json,
        get_rel_path,
    )


def _extract_message(result) -> str:
    try:
        return str(result.message)
    except AttributeError:
        return str(result)


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
            def _run_async(args: dict, _cls=target_cls) -> str:
                instance = _cls(args=args)
                result = asyncio.run(instance.execute())
                return _extract_message(result)

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


def _build_registry() -> Dict[str, dict]:
    registry: Dict[str, dict] = {}
    py_files = []

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

    return registry


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


def _load_payload(source: str) -> dict:
    stripped = source.strip()
    if stripped.endswith(".json") and exists(stripped):
        return read_json(stripped)
    return json.loads(stripped)


def dispatch(payload: dict) -> str:
    tool_name = payload.get("tool_name", "").strip()
    tool_args = payload.get("tool_args", {})

    if not tool_name:
        return "Error: `tool_name` is required in the JSON payload."

    if type(tool_args) is not dict:
        return "Error: `tool_args` must be a JSON object (dict)."

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
        return f"Error: Unknown tool '{tool_name}'. Available tools: {available}"

    normalised = {
        str(k): v if type(v) is str else str(v)
        for k, v in tool_args.items()
    }

    return registry[target_tool]["runner"](normalised)


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
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__ or "human-skills Command Center")
        print("\nUsage:")
        print("  • human-skills --list [all | <dir_name>] (or --list-all)")
        print("  • human-skills --skill_info <skill_name>")
        print("  • human-skills --tool_info <tool_name>")
        print("  • human-skills '{\"tool_name\": \"<name>\", \"tool_args\": {...}}'")
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

    source = sys.argv[1]

    try:
        payload = _load_payload(source)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    result = dispatch(payload)
    print(result)
    is_error = result.startswith("❌") or result.startswith("Error:") or result.startswith("Error ")
    sys.exit(1 if is_error else 0)


if __name__ == "__main__":
    main()
