"""
run_tool.py — Universal JSON Wrapper for Human Skills Tools
============================================================
AI agents work best with structured JSON. This wrapper accepts a JSON payload
and dispatches it to the correct tool — no CLI flags needed.

USAGE:
    python scripts/run_tool.py '<json_string>'
    python scripts/run_tool.py path/to/call.json

INPUT FORMAT:
    {
        "tool_name": "tree_gen",
        "tool_args": {
            "input_path": "/absolute/path/to/dir",
            "output_path": "/absolute/path/to/out",
            "max_depth": 4,
            "layout": "vertical",
            "use_gitignore": "true",
            "ignored_path": "/path/to/skip",
            "ignored_extensions": ".log,.tmp"
        }
    }

SUPPORTED TOOLS:
    - tree_gen  →  scripts/tree_gen.py  (TreeGen.run)

EXTENDING:
    To add a new tool, import it and add an entry to TOOL_REGISTRY below.
"""

import json
import sys
from pathlib import Path

# ── Make the scripts/ folder importable regardless of cwd ────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# ── Tool registry ─────────────────────────────────────────────────────────────
# Map tool_name → callable(args: dict) -> str
def _load_registry() -> dict:
    registry = {}

    try:
        from tree_gen import TreeGen
        registry["tree_gen"] = TreeGen.run
    except ImportError as e:
        registry["tree_gen"] = None
        _warn(f"tree_gen unavailable: {e}")

    return registry


def _warn(msg: str) -> None:
    print(f"[run_tool] WARNING: {msg}", file=sys.stderr)


# ── JSON loading ──────────────────────────────────────────────────────────────

def _load_payload(source: str) -> dict:
    """
    Accept either a raw JSON string or a path to a .json file.
    Returns the parsed dict.
    """
    stripped = source.strip()

    # Looks like a file path?
    candidate = Path(stripped)
    if candidate.suffix == ".json" and candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    # Otherwise treat as a raw JSON string
    return json.loads(stripped)


# ── Main dispatcher ───────────────────────────────────────────────────────────

def dispatch(payload: dict) -> str:
    """
    Route a payload to the correct tool and return the result string.

    Expected payload shape:
        {
            "tool_name": "<name>",
            "tool_args": { ... }
        }
    """
    tool_name = payload.get("tool_name", "").strip()
    tool_args = payload.get("tool_args", {})

    if not tool_name:
        return "Error: `tool_name` is required in the JSON payload."

    if not isinstance(tool_args, dict):
        return "Error: `tool_args` must be a JSON object (dict)."

    registry = _load_registry()

    if tool_name not in registry:
        available = ", ".join(sorted(registry.keys())) or "(none)"
        return f"Error: Unknown tool '{tool_name}'. Available: {available}"

    runner = registry[tool_name]
    if runner is None:
        return f"Error: Tool '{tool_name}' failed to load. Check its import errors above."

    # Normalise all values to strings (some tools expect str args, not int/bool)
    normalised = {k: str(v) if not isinstance(v, str) else v for k, v in tool_args.items()}

    return runner(normalised)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

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
