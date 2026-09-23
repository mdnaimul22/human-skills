import os
import json
import pickle
import shutil
from pathlib import Path
from typing import Any, Union

from .paths import PROJECT_ROOT, resolve_path, resolve_sandboxed


def _abs(relative_path: Union[str, Path]) -> Path:
    return resolve_path(relative_path)


def read_text(relative_path: Union[str, Path], encoding: str = "utf-8") -> str:
    return _abs(relative_path).read_text(encoding=encoding)


def write_text(relative_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    path = _abs(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def read_json(relative_path: Union[str, Path]) -> Any:
    return json.loads(read_text(relative_path))


def write_json(relative_path: Union[str, Path], data: Any, indent: int = 2) -> None:
    write_text(relative_path, json.dumps(data, indent=indent, ensure_ascii=False))


def read_pickle(path: Union[str, Path]) -> Any:
    with open(_abs(path), "rb") as f:
        return pickle.load(f)


def write_pickle(data: Any, path: Union[str, Path]) -> None:
    p = _abs(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        pickle.dump(data, f)


def exists(relative_path: Union[str, Path]) -> bool:
    try:
        return _abs(relative_path).exists()
    except (ValueError, OSError):
        return False


def is_file(relative_path: Union[str, Path]) -> bool:
    try:
        return _abs(relative_path).is_file()
    except (ValueError, OSError):
        return False


def is_dir(relative_path: Union[str, Path]) -> bool:
    try:
        return _abs(relative_path).is_dir()
    except (ValueError, OSError):
        return False


def ensure_dir(relative_path: Union[str, Path]) -> Path:
    path = _abs(relative_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete(relative_path: Union[str, Path]) -> None:
    path = _abs(relative_path)
    if path == PROJECT_ROOT or path == Path("/"):
        raise ValueError(f"Security violation: Cannot delete root path: {relative_path}")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def list_files(relative_path: Union[str, Path], pattern: str = "*") -> list[Path]:
    p = _abs(relative_path)
    if not p.is_dir():
        return []
    return list(p.glob(pattern))


def get_size(relative_path: Union[str, Path]) -> int:
    return os.path.getsize(_abs(relative_path))


def get_mtime(relative_path: Union[str, Path]) -> float:
    return os.path.getmtime(_abs(relative_path))


def read_from_pos(relative_path: Union[str, Path], pos: int, encoding: str = "utf-8") -> str:
    with open(_abs(relative_path), "r", encoding=encoding, errors="ignore") as f:
        f.seek(pos)
        return f.read()


def get_abs_path(*parts: str) -> str:
    if not parts:
        return str(PROJECT_ROOT)
    first = Path(parts[0]).expanduser()
    if first.is_absolute():
        return str(Path(*parts).expanduser().resolve())
    return str(PROJECT_ROOT.joinpath(*parts).resolve())


def get_rel_path(path: Union[str, Path], base: Union[str, Path, None] = None) -> str:
    if not path:
        return ""
    p_str = str(path).strip()
    base_dir = Path(base).resolve() if base else PROJECT_ROOT
    try:
        p = Path(p_str).expanduser()
        if p.is_absolute():
            return str(p.resolve().relative_to(base_dir))
    except (ValueError, OSError):
        pass

    clean_base = str(base_dir).rstrip("/")
    if p_str.startswith(clean_base + "/"):
        return p_str[len(clean_base) + 1:].lstrip("/")
    return p_str
