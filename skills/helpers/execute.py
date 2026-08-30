import sys
import json
import asyncio
import inspect
import importlib
import importlib.util
import ast
from pathlib import Path
from typing import Callable, Optional, Dict, List


_HELPERS_DIR = Path(__file__).resolve().parent
_SKILLS_DIR = _HELPERS_DIR.parent
_STORAGE_DIR = _SKILLS_DIR / "storage"

# Ensure root skills dir is always in sys.path
if str(_SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILLS_DIR))

# Exclude list
_EXCLUDED = {"execute.py", "__init__.py", "__pycache__"}


def _extract_message(result) -> str:
    """
    Accept either a plain string or a Response object.
    Returns the message string in both cases.
    """
    if isinstance(result, str):
        return result
    if hasattr(result, "message"):
        return str(result.message)
    return str(result)


def _get_category_for_path(path: Path) -> str:
    """Derive the top-level storage category for a given path."""
    try:
        rel = path.relative_to(_STORAGE_DIR)
        return rel.parts[0] if len(rel.parts) > 1 else "general"
    except Exception:
        return "other"


# ─ Resolve a single .py file → sync callable or None ──────────

def _resolve_runner(module_name: str, path: Path) -> Optional[dict]:
    """
    Searches for any class extending 'Tool' with an async execute().
    Returns a dict containing the runner and metadata.
    """
    # 1. Safely check if the file contains a Tool class via AST before executing it
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
        has_tool = any(
            isinstance(node, ast.ClassDef) and 
            any(isinstance(base, ast.Name) and base.id == 'Tool' for base in node.bases)
            for node in tree.body
        )
        if not has_tool:
            return None
    except Exception:
        pass  # Fallback to dynamic loading if AST parsing fails

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
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
                "file_path": str(path)
            }

    return None


def _build_registry() -> Dict[str, dict]:
    """
    Recursively scan _STORAGE_DIR and _SKILLS_DIR for .py files inside any 'scripts' folder
    and return a {tool_name: tool_dict} mapping.
    """
    registry: Dict[str, dict] = {}
    py_files: List[Path] = []

    # 1. Scan storage categories (e.g. storage/custom/*/scripts/*.py, storage/antv/*/scripts/*.py)
    if _STORAGE_DIR.exists():
        py_files.extend(_STORAGE_DIR.rglob("scripts/*.py"))

    # 2. Backward compatibility: Scan flat skills/*/scripts/*.py
    py_files.extend(_SKILLS_DIR.glob("*/scripts/*.py"))

    for py_file in sorted(set(py_files)):
        if py_file.name in _EXCLUDED:
            continue

        # Add the script's directory and skill directory to sys.path
        if str(py_file.parent) not in sys.path:
            sys.path.insert(0, str(py_file.parent))
        if str(py_file.parent.parent) not in sys.path:
            sys.path.insert(0, str(py_file.parent.parent))

        tool_name = py_file.stem
        runner = _resolve_runner(tool_name, py_file)

        if runner is not None:
            registry[tool_name] = runner
            
            # Also register by target class name if different
            cls_name = runner.get("name")
            if cls_name and cls_name != tool_name and cls_name not in registry:
                registry[cls_name] = runner

    return registry


def _get_categories_map() -> Dict[str, List[str]]:
    """
    Returns a dict mapping category_directory_name -> list of skill_names.
    """
    categories: Dict[str, List[str]] = {}
    if _STORAGE_DIR.exists():
        for md in sorted(_STORAGE_DIR.rglob("SKILL.md")):
            rel = md.parent.relative_to(_STORAGE_DIR)
            cat = rel.parts[0] if len(rel.parts) > 1 else "general"
            categories.setdefault(cat, []).append(md.parent.name)

    for path in sorted(_SKILLS_DIR.iterdir()):
        if path.is_dir() and path.name not in ("helpers", "storage") and (path / "SKILL.md").exists():
            categories.setdefault("other", []).append(path.name)
            
    return categories


def _build_category_index(categories_map: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Builds a lowercase / normalized lookup index mapping lowercase variations
    to the exact real on-disk directory name.
    
    Example:
      'custom' -> 'custom'
      'fission-ai _openspec' -> 'Fission-AI _OpenSpec'
      'fission-ai_openspec' -> 'Fission-AI _OpenSpec'
      'obra_ superpowers' -> 'obra_ superpowers'
      'obra_superpowers' -> 'obra_ superpowers'
    """
    index: Dict[str, str] = {}
    for real_name in categories_map.keys():
        lowered = real_name.lower()
        index[lowered] = real_name
        
        # Normalization with spaces, underscores, and hyphens
        index[lowered.replace(" ", "_")] = real_name
        index[lowered.replace(" ", "-")] = real_name
        index[lowered.replace("_", "-")] = real_name
        index[lowered.replace("-", "_")] = real_name
        
        # Stripped alphanumeric form
        stripped = lowered.replace(" ", "").replace("_", "").replace("-", "")
        index[stripped] = real_name
        
    return index


def _match_category(target: str, categories_map: Dict[str, List[str]]) -> Optional[str]:
    """
    Matches a user query (case-insensitively) against available storage category directory names
    using the lowercase index.
    """
    query = target.strip().lower()
    if not query:
        return None

    index = _build_category_index(categories_map)

    # 1. Exact lowercase match
    if query in index:
        return index[query]

    # 2. Stripped alphanumeric match
    query_norm = query.replace(" ", "").replace("_", "").replace("-", "")
    if query_norm in index:
        return index[query_norm]

    # 3. Substring / Prefix match
    matches = {real_name for k, real_name in index.items() if query_norm in k}
    if len(matches) == 1:
        return next(iter(matches))

    return None


def _find_skill_md(skill_name: str) -> Optional[Path]:
    """
    Find SKILL.md for a given skill name across all storage categories.
    Supports case-insensitive matching, direct names, and category-scoped paths.
    """
    clean_name = skill_name.strip()
    clean_lower = clean_name.lower().replace("_", "-")

    # 1. Direct path check in storage
    if _STORAGE_DIR.exists():
        storage_direct = _STORAGE_DIR / clean_name / "SKILL.md"
        if storage_direct.exists():
            return storage_direct

        # 2. Case-insensitive search recursively across storage namespaces
        for md_path in _STORAGE_DIR.rglob("SKILL.md"):
            skill_folder = md_path.parent.name
            if skill_folder.lower().replace("_", "-") == clean_lower:
                return md_path

    # 3. Direct path check in root skills dir
    root_direct = _SKILLS_DIR / clean_name / "SKILL.md"
    if root_direct.exists():
        return root_direct

    for path in _SKILLS_DIR.iterdir():
        if path.is_dir() and path.name.lower().replace("_", "-") == clean_lower and (path / "SKILL.md").exists():
            return path / "SKILL.md"

    return None


def _warn(msg: str) -> None:
    print(f"[execute] WARNING: {msg}", file=sys.stderr)


def _load_payload(source: str) -> dict:
    stripped = source.strip()
    candidate = Path(stripped)
    
    if candidate.suffix == ".json" and candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    return json.loads(stripped)


def dispatch(payload: dict) -> str:
    """Route a JSON payload to the correct tool and return the result string."""
    tool_name = payload.get("tool_name", "").strip()
    tool_args = payload.get("tool_args", {})

    if not tool_name:
        return "Error: `tool_name` is required in the JSON payload."

    if not isinstance(tool_args, dict):
        return "Error: `tool_args` must be a JSON object (dict)."

    registry = _build_registry()

    # Case-insensitive / normalized tool lookup index
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
        k: str(v) if not isinstance(v, str) else v
        for k, v in tool_args.items()
    }

    return registry[target_tool]["runner"](normalised)


def _handle_list(args: List[str]) -> None:
    """
    Handle 'human-skills --list [all | dir_name | field1,field2]' command center.
    """
    registry = _build_registry()
    categories = _get_categories_map()
    all_categories = sorted(categories.keys())

    # ── 1. Default or 'all': List all skills grouped by category ──────────────
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
                cat_label = f" ({info.get('category', 'custom')})" if info.get('category') else ""
                print(f"  • {name}{cat_label}")

        print("\n💡 Quick Navigation:")
        print("  • List specific category: human-skills --list <dir_name>  (e.g. human-skills --list custom)")
        print("  • Read skill instructions: human-skills --skill_info <skill_name>")
        print("  • Inspect tool metadata:   human-skills --tool_info <tool_name>")
        print("=" * 70)
        sys.exit(0)

    # ── 2. Directory-specific listing: human-skills --list <dir_name> ──────────
    target_query = args[0].strip()

    # Check for legacy JSON fields format (e.g. 'name,description')
    if "," in target_query and all(f.strip().lower() in ("name", "description", "arguments", "instruction", "category") for f in target_query.split(",")):
        fields = [f.strip().lower() for f in target_query.split(",")]
        output = {}
        for tool_id, tool_info in registry.items():
            tool_data = {f: tool_info.get(f, "") for f in fields}
            output[tool_id] = tool_data
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Match category using lowercase index
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
        print(f"  • Read skill documentation: human-skills --skill_info <skill_name>")
        print(f"  • Inspect tool parameters:  human-skills --tool_info <tool_name>")
        print(f"  • View all categories:      human-skills --list all")
        print("=" * 70)
        sys.exit(0)

    # ── 3. Invalid directory name: Show available directories with error ───────
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
        print("  • human-skills --list [all | <dir_name>]")
        print("  • human-skills --skill_info <skill_name>")
        print("  • human-skills --tool_info <tool_name>")
        print("  • human-skills '{\"tool_name\": \"<name>\", \"tool_args\": {...}}'")
        sys.exit(0)

    # ── 1. Skill Info Command ──────────────────────────────────────────────────
    if sys.argv[1] == "--skill_info":
        if len(sys.argv) < 3:
            print("Error: --skill_info requires a skill name.", file=sys.stderr)
            sys.exit(1)
            
        skill_name = sys.argv[2]
        skill_md_path = _find_skill_md(skill_name)
        if not skill_md_path or not skill_md_path.exists():
            print(f"Error: Skill documentation for '{skill_name}' not found.", file=sys.stderr)
            sys.exit(1)
            
        print(skill_md_path.read_text(encoding="utf-8"))
        sys.exit(0)

    # ── 2. Tool Info Command ───────────────────────────────────────────────────
    if sys.argv[1] == "--tool_info":
        if len(sys.argv) < 3:
            print("Error: --tool_info requires an exact tool name.", file=sys.stderr)
            sys.exit(1)
            
        target_tool = sys.argv[2]
        registry = _build_registry()
        
        # Lowercase index for tool lookup
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
            "category": tool_info.get("category", "")
        }
        
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # ── 3. List Command Center ─────────────────────────────────────────────────
    if sys.argv[1] == "--list":
        _handle_list(sys.argv[2:])

    # ── 4. Tool Execution Dispatcher ───────────────────────────────────────────
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
