import json
import os
import pickle
import shutil
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT


def _abs(relative_path: str) -> Path:
    return PROJECT_ROOT.safe_resolve(relative_path)


def read_text(relative_path: str, encoding: str = "utf-8") -> str:
    return _abs(relative_path).read_text(encoding=encoding)


def write_text(relative_path: str, content: str, encoding: str = "utf-8") -> None:
    path = _abs(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def read_bytes(relative_path: str) -> bytes:
    return _abs(relative_path).read_bytes()


def write_bytes(relative_path: str, data: bytes) -> None:
    path = _abs(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def read_json(relative_path: str) -> Any:
    return json.loads(read_text(relative_path))


def write_json(relative_path: str, data: Any, indent: int = 2) -> None:
    write_text(relative_path, json.dumps(data, indent=indent, ensure_ascii=False))


def read_yaml(relative_path: str) -> Any:
    import yaml
    return yaml.safe_load(read_text(relative_path))


def write_yaml(relative_path: str, data: Any) -> None:
    import yaml
    write_text(relative_path, yaml.safe_dump(data, sort_keys=False))


def read_pickle(path: str) -> Any:
    with open(_abs(path), "rb") as f:
        return pickle.load(f)


def write_pickle(data: Any, path: str) -> None:
    p = _abs(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
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
    p = _abs(relative_path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def delete(relative_path: str) -> None:
    path = _abs(relative_path)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def list_files(relative_path: str = "", pattern: str = "*") -> list[Path]:
    target = _abs(relative_path) if relative_path else PROJECT_ROOT
    if not target.exists() or not target.is_dir():
        return []
    return sorted(target.glob(pattern))


def get_size(relative_path: str) -> int:
    return _abs(relative_path).stat().st_size


def get_mtime(relative_path: str) -> float:
    return _abs(relative_path).stat().st_mtime


def read_from_pos(relative_path: str, pos: int = 0) -> tuple[str, int]:
    with open(_abs(relative_path), "r", encoding="utf-8") as f:
        f.seek(pos)
        content = f.read()
        return content, f.tell()


def get_abs_path(*parts: str | Path) -> str:
    if not parts:
        return str(PROJECT_ROOT)
    first = Path(parts[0]).expanduser()
    if first.is_absolute():
        p = Path(*parts).expanduser()
        return str(PROJECT_ROOT.safe_resolve(p))
    target = PROJECT_ROOT.joinpath(*parts)
    return str(PROJECT_ROOT.safe_resolve(target))


def is_subpath(parent: str, child: str) -> bool:
    try:
        parent_path = _abs(parent).resolve()
        child_path = _abs(child).resolve()
        return child_path.is_relative_to(parent_path)
    except (ValueError, RuntimeError):
        return False


def get_rel_path(path: str | Path, base: str | Path | None = None) -> str:
    if not path:
        return ""
    p_str = str(path).strip()
    base_dir = Path(base).resolve() if base else PROJECT_ROOT.root
    try:
        p = Path(p_str)
        if p.is_absolute():
            return str(p.resolve().relative_to(base_dir))
    except (ValueError, OSError):
        pass
    clean_base = str(base_dir).rstrip("/")
    if p_str.startswith(clean_base + "/"):
        return p_str[len(clean_base) + 1:].lstrip("/")
    return p_str
