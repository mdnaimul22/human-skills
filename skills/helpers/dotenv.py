import os
import re
from pathlib import Path
from typing import Optional

from .paths import PROJECT_ROOT
from . import files

_DEFAULT_DOTENV_PATHS = [".env", ".env.stock_resource", ".env.others"]


def load_dotenv(path: Optional[str] = None) -> None:
    targets = [path] if path else _DEFAULT_DOTENV_PATHS
    for target in targets:
        if not files.exists(target):
            continue
        for line in files.read_text(target).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def set_value(key: str, value: str, path: str = ".env") -> None:
    content = files.read_text(path) if files.exists(path) else ""
    lines = content.splitlines()
    found = False
    new_lines = []
    for line in lines:
        if re.match(rf"^\s*{re.escape(key)}\s*=", line):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    files.write_text(path, "\n".join(new_lines) + "\n")
    load_dotenv(path)


def get_value(key: str, default: str = "") -> str:
    load_dotenv()
    return os.environ.get(key, default)


def remove_value(key: str, path: str = ".env") -> None:
    if not files.exists(path):
        return
    lines = files.read_text(path).splitlines()
    new_lines = [l for l in lines if not re.match(rf"^\s*{re.escape(key)}\s*=", l)]
    files.write_text(path, "\n".join(new_lines) + "\n")