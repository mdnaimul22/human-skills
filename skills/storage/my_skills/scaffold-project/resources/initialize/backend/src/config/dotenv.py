import os
import re

from . import files

_DEFAULT_DOTENV_PATH: str = ".env"


def parse_env_dict(path: str) -> dict[str, str]:
    if not files.exists(path):
        return {}
    result: dict[str, str] = {}
    for line in files.read_text(path).splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, _, val = clean.partition("=")
        k = key.strip()
        v = val.strip().strip('"').strip("'")
        if k:
            result[k] = v
    return result


def _parse_env_file(path: str, override: bool = False) -> None:
    parsed = parse_env_dict(path)
    for key, value in parsed.items():
        if override:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)


def load_dotenv(*paths: str, override: bool = False) -> None:
    target_paths = paths if paths else (_DEFAULT_DOTENV_PATH,)
    for p in target_paths:
        if files.exists(p):
            _parse_env_file(p, override=override)
        elif p == _DEFAULT_DOTENV_PATH and files.exists(".env.example"):
            try:
                files.write_text(p, files.read_text(".env.example"))
                _parse_env_file(p, override=override)
            except Exception:
                pass


def set_value(key: str, value: str, path: str = _DEFAULT_DOTENV_PATH) -> None:
    content = files.read_text(path) if files.exists(path) else ""
    lines = content.splitlines()
    found = False
    new_lines: list[str] = []
    for line in lines:
        if re.match(rf"^\s*{re.escape(key)}\s*=", line):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    files.write_text(path, "\n".join(new_lines) + "\n")
    os.environ[key] = value


def get_value(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def sync_process_env(key: str, value: str) -> None:
    os.environ[key] = value


def remove_value(key: str, path: str = _DEFAULT_DOTENV_PATH) -> None:
    if not files.exists(path):
        return
    lines = files.read_text(path).splitlines()
    new_lines = [l for l in lines if not re.match(rf"^\s*{re.escape(key)}\s*=", l)]
    files.write_text(path, "\n".join(new_lines) + "\n")
    os.environ.pop(key, None)
