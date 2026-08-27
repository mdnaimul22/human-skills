import sys
import json
import asyncio
import inspect
import importlib
import importlib.util
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


# ─ Resolve a single .py file → sync callable or None ──────────

import ast

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
                "instruction": getattr(target_cls, "instruction", "")
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

    return registry


def _find_skill_md(skill_name: str) -> Optional[Path]:
    """
    Find SKILL.md for a given skill name across all storage categories.
    Supports both direct names ('tree_gen', 'antv-g2-chart-expert') and
    category-scoped paths ('custom/tree_gen', 'antv/antv-g2-chart-expert').
    """
    clean_name = skill_name.strip()

    # 1. Direct path check in storage
    if _STORAGE_DIR.exists():
        storage_direct = _STORAGE_DIR / clean_name / "SKILL.md"
        if storage_direct.exists():
            return storage_direct

        # 2. Search recursively across storage namespaces
        for md_path in _STORAGE_DIR.rglob("SKILL.md"):
            if md_path.parent.name == clean_name:
                return md_path

    # 3. Direct path check in root skills dir
    root_direct = _SKILLS_DIR / clean_name / "SKILL.md"
    if root_direct.exists():
        return root_direct

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

    if tool_name not in registry:
        available = ", ".join(sorted(registry.keys())) or "(none)"
        return f"Error: Unknown tool '{tool_name}'. Available tools: {available}"

    normalised = {
        k: str(v) if not isinstance(v, str) else v
        for k, v in tool_args.items()
    }

    return registry[tool_name]["runner"](normalised)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

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

    if sys.argv[1] == "--tool_info":
        if len(sys.argv) < 3:
            print("Error: --tool_info requires an exact tool name.", file=sys.stderr)
            sys.exit(1)
            
        target_tool = sys.argv[2]
        registry = _build_registry()
        
        if target_tool not in registry:
            print(f"Error: Tool '{target_tool}' not found.", file=sys.stderr)
            sys.exit(1)
            
        tool_info = registry[target_tool]
        output = {
            "name": tool_info.get("name", ""),
            "description": tool_info.get("description", ""),
            "arguments": tool_info.get("arguments", ""),
            "instruction": tool_info.get("instruction", "")
        }
        
        print(json.dumps(output, indent=2))
        sys.exit(0)

    if sys.argv[1] == "--list":
        registry = _build_registry()
        
        fields = sys.argv[2:]
        if not fields:
            # Group skills by storage category
            categories: Dict[str, List[str]] = {}
            if _STORAGE_DIR.exists():
                for md in sorted(_STORAGE_DIR.rglob("SKILL.md")):
                    rel = md.parent.relative_to(_STORAGE_DIR)
                    cat = rel.parts[0] if len(rel.parts) > 1 else "general"
                    categories.setdefault(cat, []).append(md.parent.name)

            for path in sorted(_SKILLS_DIR.iterdir()):
                if path.is_dir() and path.name not in ("helpers", "storage") and (path / "SKILL.md").exists():
                    categories.setdefault("other", []).append(path.name)
            
            total_skills = sum(len(v) for v in categories.values())
            if total_skills > 0:
                print(f"Available Skills ({total_skills} total across {len(categories)} categories):")
                for cat, skills in sorted(categories.items()):
                    print(f"\n  📁 [{cat}] ({len(skills)} skills)")
                    for skill in sorted(skills):
                        print(f"     • {skill}")
                print("")
                
            if not registry:
                print("No tools discovered.")
            else:
                print(f"Discovered Tools ({len(registry)} total):")
                for name in sorted(registry.keys()):
                    print(f"  • {name}")
                    
            print("\nFor more details instruction execute: human-skills --tool_info {exact_tool_name}")
            print(
                "For Proper Skill usages instruction run: human-skills --skill_info {skill_name}\n"
                "Example_1: human-skills --skill_info zram-optimizer\n"
                "Example_2: human-skills --skill_info antv-g2-chart-expert"
            )
            sys.exit(0)
            
        if not registry:
            print("No tools discovered.", file=sys.stderr)
            sys.exit(0)
            
        output = {}
        for tool_id, tool_info in registry.items():
            tool_data = {}
            for field in fields:
                field_clean = field.strip(",").lower()
                if field_clean in ("runner",):
                    continue
                tool_data[field_clean] = tool_info.get(field_clean, "")
            output[tool_id] = tool_data
            
        print(json.dumps(output, indent=2))
        sys.exit(0)

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
