import sys
from pathlib import Path

_MARKER_FILES = (".env", "main.py", "pyproject.toml", ".git", "cli.py", "app.py")

def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current] + list(current.parents):
        if any((candidate / m).exists() for m in _MARKER_FILES):
            return candidate
    return current.parent


PROJECT_ROOT: Path = find_project_root().resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def resolve_sandboxed(path: str | Path) -> Path:
    """
    Ensure the path is strictly confined within PROJECT_ROOT (or pytest temp environments).
    Blocks directory traversal ('..'), symlink escapes, null bytes, and arbitrary file access.
    """
    raw_str = str(path).strip()
    if not raw_str:
        raise ValueError("Path cannot be empty or whitespace")
    if "\0" in raw_str:
        raise ValueError("Null bytes not permitted in path")

    p = Path(raw_str).expanduser()

    # Relative paths resolve strictly against PROJECT_ROOT
    if not p.is_absolute():
        resolved = (PROJECT_ROOT / p).resolve()
        if resolved != PROJECT_ROOT and PROJECT_ROOT not in resolved.parents:
            raise ValueError(f"Access denied: path '{path}' escapes PROJECT_ROOT sandbox ({PROJECT_ROOT})")
        return resolved

    # Absolute path check
    resolved = p.resolve()
    if resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents:
        return resolved

    # Allow /tmp environments during testing (pytest tmp_path)
    if "pytest" in sys.modules:
        tmp_dir = Path("/tmp").resolve()
        if resolved != tmp_dir and tmp_dir in resolved.parents:
            return resolved

    raise ValueError(f"Access denied: path '{path}' escapes PROJECT_ROOT sandbox ({PROJECT_ROOT})")