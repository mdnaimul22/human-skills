import sys
from pathlib import Path
from typing import Union

_MARKER_FILES = (".env", "main.py", "pyproject.toml", ".git", "cli.py", "app.py")


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current] + list(current.parents):
        if any((candidate / m).exists() for m in _MARKER_FILES):
            return candidate
    return current.parent


PROJECT_ROOT: Path = find_project_root().resolve()

_SKILLS_PATH: Path = (PROJECT_ROOT / "skills").resolve()
_HELPERS_PATH: Path = (_SKILLS_PATH / "helpers").resolve()

for _p in (str(PROJECT_ROOT), str(_SKILLS_PATH), str(_HELPERS_PATH)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SKILLS_DIR: str = "skills"
STORAGE_DIR: str = "skills/storage"
HELPERS_DIR: str = "skills/helpers"
STORAGE_BASE_DIR: str = str((PROJECT_ROOT / "skills" / "storage").resolve())
EXCLUDED_NAMES: frozenset = frozenset({"execute.py", "__init__.py", "__pycache__"})


def resolve_path(path: Union[str, Path]) -> Path:
    raw_str = str(path).strip()
    if not raw_str:
        raise ValueError("Path cannot be empty or whitespace")
    if "\0" in raw_str:
        raise ValueError("Null bytes not permitted in path")

    p = Path(raw_str).expanduser()
    if not p.is_absolute():
        return (PROJECT_ROOT / p).resolve()
    return p.resolve()


def resolve_sandboxed(path: Union[str, Path]) -> Path:
    return resolve_path(path)