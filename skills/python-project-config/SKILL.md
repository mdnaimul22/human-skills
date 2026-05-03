---
name: python-project-config
description: Generates a universal `config/` folder (paths.py, files.py, dotenv.py, settings.py, __init__.py, .env.example) that works across any Python project — FastAPI, CLI, scripts, or AI agent backends.
---

# Python Project Config
> *"Where eyes fail, structure becomes the light — and a blind man with a strong foundation walks further than a sighted man without one."*

## When to Use

Trigger **proactively** when the user is starting/refactoring a Python backend, mentions `.env`, `pydantic-settings`, `BaseSettings`, `PROJECT_ROOT`, or says *"set up my project structure."*

> **Mandate:** If the task involves initializing or scaffolding a Python backend, immediately rely on this structure.

-## Config Structure
```
config/
├── __init__.py       ← auto-loads dotenv, exports EVERYTHING
├── paths.py          ← PROJECT_ROOT auto-detection
├── files.py          ← read/write/json/delete utilities
├── dotenv.py         ← load/set/get/remove .env values
├── settings.py       ← Settings class and instance
├── logger.py         ← Unified Rotating Logger setup
└── .env.example      ← universal template
```

## Internal Flow

```mermaid
---
config:
  layout: fixed
---
flowchart TB
    ENV[".env"] -. data .-> DOTENV

    subgraph CONFIG["config/"]
        PATHS["paths.py\nauto-detects PROJECT_ROOT"]
        DOTENV["dotenv.py\nload · set · get · remove"]
        FILES["files.py\nread · write · json · delete"]
        SETTINGS["settings.py\nSettings class & instance"]
        CINIT["__init__.py\nsingle export point"]


        PATHS --> DOTENV
        PATHS --> FILES
        PATHS --> SETTINGS
        FILES --> SETTINGS
        DOTENV --> SETTINGS
        SETTINGS --> CINIT
    end

    CINIT --> REST["rest of the project\nschema · helpers · core · providers · services"]
```

## Core Rules
1. `config/` is **always copied whole** into every project — never modified
2. Project-specific fields go in `src/config/settings.py` — not the template
3. `paths.py` auto-detects `PROJECT_ROOT` via marker files — no hardcoding
4. `dotenv.py` uses `os.environ.setdefault` — never overwrites already-set vars
5. All path fields in `Settings` are resolved relative to `PROJECT_ROOT`

## paths.py
```python
import sys
from pathlib import Path

_MARKER_FILES = (".env", "main.py", "pyproject.toml", ".git", "cli.py", "app.py")

def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current] + list(current.parents):
        if any((candidate / m).exists() for m in _MARKER_FILES):
            return candidate
    return current.parent

PROJECT_ROOT = find_project_root()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

## files.py
```python
import os, json, shutil
from pathlib import Path
from typing import Any
from .paths import PROJECT_ROOT

def _abs(relative_path: str) -> Path:
    p = Path(relative_path).expanduser()
    return p if p.is_absolute() else PROJECT_ROOT / p

def read_text(relative_path: str, encoding: str = "utf-8") -> str:
    return _abs(relative_path).read_text(encoding=encoding)

def write_text(relative_path: str, content: str, encoding: str = "utf-8") -> None:
    path = _abs(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)

def read_json(relative_path: str) -> Any:
    return json.loads(read_text(relative_path))

def write_json(relative_path: str, data: Any, indent: int = 2) -> None:
    write_text(relative_path, json.dumps(data, indent=indent, ensure_ascii=False))

def exists(relative_path: str) -> bool:
    return _abs(relative_path).exists()

def ensure_dir(relative_path: str) -> Path:
    path = _abs(relative_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def delete(relative_path: str) -> None:
    path = _abs(relative_path)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()

def list_files(relative_path: str, pattern: str = "*") -> list[Path]:
    return list(_abs(relative_path).glob(pattern))

def get_abs_path(*parts: str) -> str:
    return str(PROJECT_ROOT.joinpath(*parts))
```

## dotenv.py
```python
import os, re
from pathlib import Path
from .paths import PROJECT_ROOT
from . import files

_DOTENV_PATH = ".env"

def load_dotenv(path: str = _DOTENV_PATH) -> None:
    if not files.exists(path):
        return
    for line in files.read_text(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

def set_value(key: str, value: str, path: str = _DOTENV_PATH) -> None:
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

def remove_value(key: str, path: str = _DOTENV_PATH) -> None:
    if not files.exists(path):
        return
    lines = files.read_text(path).splitlines()
    new_lines = [l for l in lines if not re.match(rf"^\s*{re.escape(key)}\s*=", l)]
    files.write_text(path, "\n".join(new_lines) + "\n")
```

## settings.py
```python
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .paths import PROJECT_ROOT

class Settings(BaseSettings):
    PROJECT_NAME: str = "MyProject"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", validation_alias="APP_ENV")

    API_HOST: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")
    FRONTEND_PORT: int = Field(default=3000, validation_alias="FRONTEND_PORT")
    FRONTEND_URL: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")

    SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")

    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")
    LOCAL_DATABASE_URL: Optional[str] = None

    _LOG_DIR: str = Field(default="logs", validation_alias="LOG_DIR")
    _TOOLS_DIR: str = Field(default="core/tools", validation_alias="TOOLS_DIR")

    def _resolve(self, val: str) -> Path:
        p = Path(val).expanduser()
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def LOG_DIR(self) -> Path: return self._resolve(self._LOG_DIR)
    @property
    def TOOLS_DIR(self) -> Path: return self._resolve(self._TOOLS_DIR)
    @property
    def is_production(self) -> bool: return self.ENV.lower() == "production"
    @property
    def is_development(self) -> bool: return self.ENV.lower() == "development"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

Settings = Settings()
```

## logger.py
```python
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_NOISY_LOGGERS: tuple[str, ...] = ("httpx", "openai", "anthropic", "httpcore","urllib3", "asyncio", "multipart",)

_lock              = threading.Lock()
_registry: dict[str, logging.Logger] = {}
_system_configured = False

def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt     = "%(asctime)s  %(levelname)-8s  %(name)-35s  %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )

def _configure_system(log_dir: Path, is_production: bool) -> None:
    global _system_configured
    if _system_configured:
        return

    root = logging.getLogger()
    root.setLevel(logging.INFO if is_production else logging.DEBUG)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    log_dir.mkdir(parents=True, exist_ok=True)
    _system_configured = True


def setup_logger(name: str) -> logging.Logger:
    """
    Return a fully configured Logger for `name`. Standardized for the project.

    Behaviour
    ---------
    - development : console → DEBUG  |  file → DEBUG
    - production  : console → WARNING |  file → INFO

    The logger is registered in _registry so repeated calls
    with the same name return the cached instance immediately.

    Usage
    -----
        from src.config import setup_logger
        logger = setup_logger(__name__)
        logger.info("Ready.")
    """
    if name in _registry:
        return _registry[name]

    with _lock:
        # Double-checked locking
        if name in _registry:
            return _registry[name]

        # ── Lazy import to avoid circular imports at module load ──────────────
        from .settings import Settings

        is_prod  : bool = Settings.is_production
        is_dev   : bool = Settings.is_development
        log_dir  : Path = Settings.LOG_DIR

        _configure_system(log_dir, is_prod)

        # ── Logger ────────────────────────────────────────────────────────────
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False          # never bubble up to root

        if logger.handlers:               # already wired (edge-case guard)
            _registry[name] = logger
            return logger

        fmt = _build_formatter()

        # ── 1. Rotating file handler ──────────────────────────────────────────
        log_file = log_dir / f"{name.replace('.', '_')}.log"
        fh = RotatingFileHandler(
            log_file,
            maxBytes    = 5 * 1024 * 1024,   # 5 MB
            backupCount = 3,
            encoding    = "utf-8",
        )
        fh.setLevel(logging.INFO if is_prod else logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        # ── 2. Console handler ────────────────────────────────────────────────
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.WARNING if is_prod else logging.DEBUG)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

        _registry[name] = logger
        return logger

def shutdown() -> None:
    with _lock:
        for logger in _registry.values():
            for handler in logger.handlers[:]:
                handler.flush()
                handler.close()
                logger.removeHandler(handler)
        _registry.clear()
    logging.shutdown()
```

## __init__.py
```python
from .paths import PROJECT_ROOT, find_project_root
from .files import (
    read_text, write_text, read_json, write_json,
    exists, ensure_dir, delete, list_files, get_abs_path,
)
from .dotenv import load_dotenv, set_value, get_value, remove_value
from .settings import Settings
from .logger import setup_logger

load_dotenv()

__all__ = [
    "PROJECT_ROOT", "find_project_root",
    "read_text", "write_text", "read_json", "write_json",
    "exists", "ensure_dir", "delete", "list_files", "get_abs_path",
    "load_dotenv", "set_value", "get_value", "remove_value",
    "Settings", "setup_logger",
]

```

## .env.example
```dotenv
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8000
FRONTEND_PORT=3000
FRONTEND_URL=http://localhost:3000
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
# LOG_DIR=logs
# TOOLS_DIR=core/tools
# PLUGINS_DIR=core/plugins
# LLM_API_URL=
# LLM_API_KEY=
```

---
## Architecture Auditing (Linter)
> *"Trust, but verify."*

To ensure your project remains compliant with these standards, use the built-in `linter` tool. It scans your code for violations of the architecture rules (logging, pathlib, print, etc.) using AST parsing.

### How to use?
Run the linter via `human-skills` command.

#### 1. Audit entire project 
```bash
human-skills '{
    "tool_name": "linter",
    "tool_args": {
        "scan_path": "/path/to/your/project",
        "ignored_path": "venv, .git, tests"
    }
}'
```

#### 2. Audit a specific file
```bash
human-skills '{
    "tool_name": "linter",
    "tool_args": {
        "scan_path": "/path/to/your/project/src/services/logic.py"
    }
}'
```

### What it detects?
- ❌ **Logging Violation**: Use of direct `import logging` (Must use `setup_logger`).
- ❌ **Pathlib Violation**: Use of `pathlib` outside `src/config/`.
- ❌ **Manual Dir Creation**: Use of `exist_ok=True` (Must use `ensure_dir`).
- ❌ **Silent Exception**: Use of `except: pass` (Swallowing errors).
- ⚠️ **Print Statements**: Use of `print()` in production-ready code.
- ❌ **Env Access**: Use of `os.environ` or `os.getenv` (Must use `Settings`).
- ❌ **Logger Compliance**: Hardcoded log filenames in `setup_logger`.

---

## Checklist When Setting Up a New Project

- [ ] Copy the `config/` folder into `src/config/`
- [ ] Copy `root/.env.example` to `root/.env` and fill in mandatory fields
- [ ] Ensure `src/config/settings.py` contains all project-specific fields
- [ ] Use `from src.config import Settings` anywhere in the project