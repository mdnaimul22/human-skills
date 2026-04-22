---
name: python-project-config
description: Generates a universal `config/` folder (paths.py, files.py, dotenv.py,
  settings.py, __init__.py, .env.example) that works across any Python project
  — FastAPI, CLI, scripts, or AI agent backends.
---

# Python Project Config
> *"Where eyes fail, structure becomes the light — and a blind man with a strong foundation walks further than a sighted man without one."*

## When to Use

Trigger this skill **proactively** (without waiting for explicit requests) under any of the following scenarios:

- **Project Initialization & Refactoring:** The user is starting a new Python project, restructuring an existing one, or asking how to organize `config` and `settings`.
- **Framework Setup:** The user is bootstrapping a FastAPI application, CLI tool, or AI-agent backend.
- **Environment Management:** The task involves `.env` handling, securely managing API keys, detecting universal `PROJECT_ROOT`, or organizing project-level file paths.
- **Target Keywords:** The user mentions `pydantic-settings`, `BaseSettings`, or custom configuration managers.
- **Conversational Cues:** The user says things like *"set up my project structure," "where should I put settings?," "how do I manage env vars in Python?,"* or *"copy the config folder."*

> **Mandate:** If the task involves initializing or scaffolding a Python backend, immediately rely on this structure.

## What This Config Pattern Does

Generates a universal `config/` folder that works across any Python project
(FastAPI, CLI, scripts, Next.js+Python hybrid). The folder is copied as-is
into each new project. Project-specific settings extend `BaseProjectSettings`.

---

## File Structure

```
config/
├── __init__.py       ← auto-loads dotenv, exports EVERYTHING (ProjectSettings, settings, paths, files, etc.)
├── paths.py          ← PROJECT_ROOT auto-detection
├── files.py          ← read/write/json/delete utilities
├── dotenv.py         ← load/set/get/remove .env values
├── settings.py       ← Settings class and instance
└── .env.example      ← universal template
```


---

## Config Internal Flow

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

---

## Core Rules

1. `config/` is **always copied whole** into every project — never modified
2. Project-specific fields live in `src/config/settings.py` (which extends the template) 
   or in a dedicated module that **exports via __init__.py**.

3. `paths.py` auto-detects `PROJECT_ROOT` via marker files — no hardcoding
4. `dotenv.py` uses `os.environ.setdefault` — never overwrites already-set vars
5. All path fields in settings are resolved relative to `PROJECT_ROOT`

---

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

---

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

---

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

---

## settings.py (Settings)


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

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_V1_STR: str = "/v1"
    FRONTEND_PORT: int = 3000
    FRONTEND_URL: str = "http://localhost:3000"

    SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    DATABASE_URL: str = Field(...)
    DIRECT_DATABASE_URL: Optional[str] = None
    LOCAL_DATABASE_URL: Optional[str] = None

    _LOG_DIR: str = Field(default="logs", validation_alias="LOG_DIR")
    _CACHE_DIR: Optional[str] = Field(default=None, validation_alias="CACHE_DIR")
    _TOOLS_DIR: str = Field(default="core/tools", validation_alias="TOOLS_DIR")
    _PLUGINS_DIR: str = Field(default="core/plugins", validation_alias="PLUGINS_DIR")
    _MANIFEST_PATH: Optional[str] = Field(default=None, validation_alias="MANIFEST_PATH")

    def _resolve(self, val: str) -> Path:
        p = Path(val).expanduser()
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def LOG_DIR(self) -> Path:
        return self._resolve(self._LOG_DIR)

    @property
    def CACHE_DIR(self) -> Path:
        return self._resolve(self._CACHE_DIR) if self._CACHE_DIR else self.LOG_DIR / ".cache"

    @property
    def TOOLS_DIR(self) -> Path:
        return self._resolve(self._TOOLS_DIR)

    @property
    def PLUGINS_DIR(self) -> Path:
        return self._resolve(self._PLUGINS_DIR)

    @property
    def MANIFEST_PATH(self) -> Path:
        return self._resolve(self._MANIFEST_PATH) if self._MANIFEST_PATH else self.CACHE_DIR / "manifest.json"

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "development"

    LLM_API_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_PRIMARY_MODEL: str = "gpt-4o-mini"
    LLM_FALLBACK_MODEL: Optional[str] = None
    LLM_LOCAL_MODEL: str = "qwen2.5:1.5b"

    EMBED_PROVIDERS: str = "ollama"
    EMBED_TRUNCATE: int = 4096
    EMBED_OLLAMA_URL: Optional[str] = None
    EMBED_OLLAMA_MODEL: str = "all-minilm"
    EMBED_GOOGLE_API_KEY: Optional[str] = None
    EMBED_GOOGLE_MODEL: str = "text-embedding-004"
    EMBED_JINA_API_KEY: Optional[str] = None
    EMBED_VOYAGE_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


Settings = Settings()
```


---

## __init__.py

```python
from .paths import PROJECT_ROOT, find_project_root
from .files import (
    read_text, write_text, read_json, write_json,
    exists, ensure_dir, delete, list_files, get_abs_path,
)
from .dotenv import load_dotenv, set_value, get_value, remove_value
from .settings import Settings

load_dotenv()

__all__ = [
    "PROJECT_ROOT", "find_project_root",
    "read_text", "write_text", "read_json", "write_json",
    "exists", "ensure_dir", "delete", "list_files", "get_abs_path",
    "load_dotenv", "set_value", "get_value", "remove_value",
    "Settings",
]
```


---

## How to use the config?

Import from the package root only. **Directly importing internal scripts (settings.py, paths.py) is strictly forbidden.**

```python
from src.config import Settings

print(Settings.PROJECT_ROOT)
print(Settings.LOG_DIR)
```


---

## .env.example (template)

```dotenv
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8000
FRONTEND_PORT=3000
FRONTEND_URL=http://localhost:3000

SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# LOG_DIR=logs
# CACHE_DIR=
# TOOLS_DIR=core/tools
# PLUGINS_DIR=core/plugins

# LLM_API_URL=
# LLM_API_KEY=
# LLM_PRIMARY_MODEL=gpt-4o-mini

# EMBED_PROVIDERS=ollama
# EMBED_OLLAMA_URL=http://localhost:11434
# EMBED_GOOGLE_API_KEY=

# --- Project-specific keys below ---
```

---

## Checklist When Setting Up a New Project

- [ ] Copy the `config/` folder into `src/config/`
- [ ] Copy `root/.env.example` to `root/.env` and fill in mandatory fields
- [ ] Ensure `src/config/settings.py` contains all project-specific fields
- [ ] Use `from src.config import Settings` anywhere in the project