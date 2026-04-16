"""
run_tool.py — Universal JSON Wrapper for Human Skills Tools
============================================================
AI agents work best with structured JSON. This wrapper accepts a JSON payload
and dispatches it to the correct tool — no CLI flags needed.

AUTO-DISCOVERY:
    Any .py file placed in the same `scripts/` directory is automatically
    detected as a tool if it follows the Agent Zero tool convention:

        class MyTool(Tool):
            async def execute(self, **kwargs) -> Response: ...

        Requirements:
          • Class name must be CamelCase of the filename
            (e.g. manage_project.py → ManageProject)
          • helpers/tool.py shim must be present in this directory
            (provides Tool + Response without Agent Zero runtime)

    Tool name = filename without .py  (e.g. tree_gen.py → "tree_gen")

USAGE:
    python scripts/run_tool.py '<json_string>'
    python scripts/run_tool.py path/to/call.json

INPUT FORMAT:
    {
        "tool_name": "tree_gen",
        "tool_args": {
            "input_path": "/absolute/path/to/dir",
            "max_depth":  "4"
        }
    }

LIST AVAILABLE TOOLS:
    python scripts/run_tool.py --list
"""

import asyncio
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable, Optional

# ── Ensure scripts/ is importable regardless of cwd ──────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# ── Files that are never treated as tools ────────────────────────────────────
_EXCLUDED = {"run_tool.py", "__init__.py"}


# ── Convention helpers ────────────────────────────────────────────────────────

def _to_camel(snake: str) -> str:
    """Convert 'tree_gen' → 'TreeGen'."""
    return "".join(part.capitalize() for part in snake.split("_"))


def _extract_message(result) -> str:
    """
    Accept either a plain string or an Agent Zero Response object.
    Returns the message string in both cases.
    """
    if isinstance(result, str):
        return result
    if hasattr(result, "message"):
        return str(result.message)
    return str(result)


# ── Resolve a single .py file → sync callable or None ────────────────────────

def _resolve_runner(module_name: str, path: Path) -> Optional[Callable]:
    """
    Try to import `path` as `module_name` and extract a runner callable.
    
    Expects an Agent Zero style class: module.CamelCase.execute
    Returns a unified sync callable: runner(args: dict) -> str
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)          # type: ignore[union-attr]
    except Exception as exc:
        _warn(f"Failed to load '{module_name}': {exc}")
        return None

    class_name = _to_camel(module_name)
    cls = getattr(module, class_name, None)

    if cls is not None:
        execute_method = getattr(cls, "execute", None)
        if callable(execute_method):
            def _run_async(args: dict, _cls=cls) -> str:
                # Agent Zero tools expect tool arguments inside self.args
                instance = _cls(args=args)
                result = asyncio.run(instance.execute())
                return _extract_message(result)
            return _run_async

    return None


# ── Auto-discover all tools in scripts/ ──────────────────────────────────────

def _build_registry() -> dict[str, Callable]:
    """
    Scan _SCRIPTS_DIR for .py files and return a {tool_name: runner} dict.
    Files listed in _EXCLUDED are skipped.
    """
    registry: dict[str, Callable] = {}

    for py_file in sorted(_SCRIPTS_DIR.glob("*.py")):
        if py_file.name in _EXCLUDED:
            continue

        tool_name = py_file.stem
        runner = _resolve_runner(tool_name, py_file)

        if runner is not None:
            registry[tool_name] = runner
        else:
            _warn(
                f"'{py_file.name}' found but no valid tool detected — skipped.\n"
                f"  Expected: class {_to_camel(tool_name)}(Tool) with an async execute() method."
            )

    return registry


def _warn(msg: str) -> None:
    print(f"[run_tool] WARNING: {msg}", file=sys.stderr)


# ── JSON loading ──────────────────────────────────────────────────────────────

def _load_payload(source: str) -> dict:
    """Accept a raw JSON string or a path to a .json file."""
    stripped = source.strip()
    candidate = Path(stripped)
    if candidate.suffix == ".json" and candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(stripped)


# ── Main dispatcher ───────────────────────────────────────────────────────────

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

    # Normalise all values to strings for consistent arg handling
    normalised = {
        k: str(v) if not isinstance(v, str) else v
        for k, v in tool_args.items()
    }

    return registry[tool_name](normalised)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    if sys.argv[1] == "--list":
        registry = _build_registry()
        if not registry:
            print("No tools discovered.")
        else:
            print("Discovered tools:")
            for name in sorted(registry.keys()):
                print(f"  • {name}")
        sys.exit(0)

    source = sys.argv[1]

    try:
        payload = _load_payload(source)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    result = dispatch(payload)
    print(result)
    sys.exit(0 if result.startswith("✅") else 1)


if __name__ == "__main__":
    main()
