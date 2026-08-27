import os
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Optional


def get_base_dir() -> str:
    """Get the base working directory for Agent Zero / current environment."""
    env_root = os.environ.get("A0_ROOT") or os.environ.get("AGENT_ZERO_ROOT")
    if env_root and os.path.isdir(env_root):
        return os.path.abspath(env_root)
    return os.path.abspath(os.getcwd())


def get_abs_path(*parts: str) -> str:
    """Resolve absolute path from parts relative to base directory."""
    if not parts or not any(parts):
        return get_base_dir()
    
    # If first part is already absolute
    first = str(parts[0])
    if os.path.isabs(first):
        return os.path.abspath(os.path.join(*[str(p) for p in parts if p]))
    
    return os.path.abspath(os.path.join(get_base_dir(), *[str(p) for p in parts if p]))


def read_file(path: str) -> str:
    """Read a text file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    """Write content to a file, creating parent directories if needed."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_dir(path: str) -> None:
    """Create directory and parent directories if they do not exist."""
    os.makedirs(path, exist_ok=True)


def create_dir_safe(path: str, rename_format: str = "{name}_{number}") -> str:
    """Create directory safely. If exists, generates an incremented name."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        os.makedirs(abs_path, exist_ok=True)
        return abs_path

    # Directory already exists — increment
    parent = os.path.dirname(abs_path)
    name = os.path.basename(abs_path)
    counter = 1
    while True:
        new_name = rename_format.format(name=name, number=counter)
        new_path = os.path.join(parent, new_name)
        if not os.path.exists(new_path):
            os.makedirs(new_path, exist_ok=True)
            return new_path
        counter += 1


def delete_dir(path: str) -> None:
    """Recursively delete a directory if it exists."""
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def basename(path: str) -> str:
    """Return the final component of a pathname."""
    return os.path.basename(os.path.normpath(path))


def is_in_dir(sub_path: str, parent_path: str) -> bool:
    """Check if sub_path is inside parent_path."""
    try:
        rel = os.path.relpath(os.path.abspath(sub_path), os.path.abspath(parent_path))
        return not rel.startswith("..") and not os.path.isabs(rel)
    except Exception:
        return False


def fix_dev_path(path: str) -> str:
    """Normalize and clean development paths."""
    return os.path.normpath(path)


def normalize_a0_path(path: str) -> str:
    """Convert absolute system paths into clean relative/A0 paths."""
    base = get_base_dir()
    if path.startswith(base):
        rel = os.path.relpath(path, base)
        return f"/a0/{rel}".replace("//", "/")
    return path


def read_text_files_in_dir(dir_path: str, pattern: str = "*.md") -> Dict[str, str]:
    """Read all matching text files in a directory into a {filename: content} dict."""
    result: Dict[str, str] = {}
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return result

    for entry in os.listdir(dir_path):
        full_path = os.path.join(dir_path, entry)
        if os.path.isfile(full_path):
            if pattern == "*" or fnmatch_check(entry, pattern):
                try:
                    result[entry] = read_file(full_path)
                except Exception:
                    pass
    return result


def list_files_in_dir_recursively(dir_path: str) -> List[str]:
    """List all file paths recursively within a directory."""
    files_list: List[str] = []
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return files_list

    for root, _, filenames in os.walk(dir_path):
        for f in filenames:
            files_list.append(os.path.join(root, f))
    return files_list


def fnmatch_check(filename: str, pattern: str) -> bool:
    import fnmatch
    return fnmatch.fnmatch(filename, pattern)


def read_prompt_file(filename: str, _directories: Optional[List[str]] = None, **kwargs) -> str:
    """Read a template/prompt file and format with kwargs."""
    for d in (_directories or ["prompts", "templates"]):
        candidate = os.path.join(get_base_dir(), d, filename)
        if os.path.exists(candidate):
            content = read_file(candidate)
            for k, v in kwargs.items():
                content = content.replace(f"{{{k}}}", str(v))
            return content
    return ""
