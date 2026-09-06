import os
import json
import pickle
import shutil
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT, resolve_sandboxed

# Core protected directories that cannot be deleted or overwritten via files.py
_PROTECTED_DIRS = {PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT / ".git"}


def _abs(relative_path: str) -> Path:
    return resolve_sandboxed(relative_path)


def read_text(relative_path: str, encoding: str = "utf-8") -> str:
    return _abs(relative_path).read_text(encoding=encoding)


def write_text(relative_path: str, content: str, encoding: str = "utf-8") -> None:
    path = _abs(relative_path)
    # Prevent modifying application source code
    if path == PROJECT_ROOT or (PROJECT_ROOT / "src") in path.parents or path == (PROJECT_ROOT / "src"):
        raise ValueError(f"Access denied: modifying source directory is forbidden: {relative_path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def read_json(relative_path: str) -> Any:
    return json.loads(read_text(relative_path))


def write_json(relative_path: str, data: Any, indent: int = 2) -> None:
    write_text(relative_path, json.dumps(data, indent=indent, ensure_ascii=False))


def read_pickle(path: str) -> Any:
    with open(_abs(path), 'rb') as f:
        return pickle.load(f)


def write_pickle(data: Any, path: str) -> None:
    p = _abs(path)
    # Prevent modifying application source code
    if p == PROJECT_ROOT or (PROJECT_ROOT / "src") in p.parents or p == (PROJECT_ROOT / "src"):
        raise ValueError(f"Access denied: modifying source directory is forbidden: {path}")
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'wb') as f:
        pickle.dump(data, f)


def exists(relative_path: str) -> bool:
    try:
        return _abs(relative_path).exists()
    except (ValueError, OSError):
        return False


def is_file(relative_path: str) -> bool:
    try:
        return _abs(relative_path).is_file()
    except (ValueError, OSError):
        return False


def is_dir(relative_path: str) -> bool:
    try:
        return _abs(relative_path).is_dir()
    except (ValueError, OSError):
        return False


def ensure_dir(relative_path: str) -> Path:
    path = _abs(relative_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete(relative_path: str) -> None:
    path = _abs(relative_path)
    # Self-destruction and critical directory guard
    if path in _PROTECTED_DIRS or (PROJECT_ROOT / "src") in path.parents or (PROJECT_ROOT / ".git") in path.parents:
        raise ValueError(f"Security violation: Cannot delete protected path: {relative_path}")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def list_files(relative_path: str, pattern: str = "*") -> list[Path]:
    return list(_abs(relative_path).glob(pattern))


def get_size(relative_path: str) -> int:
    return os.path.getsize(_abs(relative_path))


def get_mtime(relative_path: str) -> float:
    return os.path.getmtime(_abs(relative_path))


def read_from_pos(relative_path: str, pos: int, encoding: str = "utf-8") -> str:
    with open(_abs(relative_path), "r", encoding=encoding, errors="ignore") as f:
        f.seek(pos)
        return f.read()


def get_abs_path(*parts: str) -> str:
    if not parts:
        return str(PROJECT_ROOT)
    first = Path(parts[0]).expanduser()
    if first.is_absolute():
        p = Path(*parts).expanduser()
        return str(resolve_sandboxed(p))
    target = PROJECT_ROOT.joinpath(*parts)
    return str(resolve_sandboxed(target))
