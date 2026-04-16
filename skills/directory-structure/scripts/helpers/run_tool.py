import sys
import json
import asyncio
import inspect
import importlib
import importlib.util
from pathlib import Path
from typing import Callable, Optional


_HELPERS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _HELPERS_DIR.parent

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# excude list
_EXCLUDED = {"run_tool.py", "__init__.py"}


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

def _resolve_runner(module_name: str, path: Path) -> Optional[Callable]:
    """
    Searches for any class extending 'Tool' with an async execute().
    Returns a callable: runner(args: dict) -> str
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
                # Agent Zero tools expect tool arguments inside self.args
                instance = _cls(args=args)
                result = asyncio.run(instance.execute())
                return _extract_message(result)
            return _run_async

    return None


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
                f"  Expected: class AnyName(Tool) with an async execute() method."
            )

    return registry


def _warn(msg: str) -> None:
    print(f"[run_tool] WARNING: {msg}", file=sys.stderr)


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

    return registry[tool_name](normalised)



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
