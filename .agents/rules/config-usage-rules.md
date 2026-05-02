---
trigger: always_on
name: config-usage-rules
description: Strict usage rules for Settings and Logger — wrong patterns vs correct patterns for every scenario.
---

# Config Usage Rules: Settings & Logger

> **One rule for both: always import from `src.config`. Never bypass, never duplicate, never scatter.**

---

## Part 1 — Settings Usage Rules

`Settings` is the **single source of truth** for all configuration. Every constant, URL, path, key, timeout, or flag that could change between environments belongs in `Settings`.

---

### ❌ Hardcoding values
```python
# FORBIDDEN — scattered constants across modules
LOG_DIR = "/home/user/logs"         # hardcoded absolute path
TIMEOUT = 30                         # magic number
MODEL = "gpt-4o"                     # hardcoded model
API_URL = "http://127.0.0.1:8000"   # environment-specific value
```
```python
# ✅ CORRECT — everything through Settings
from src.config import Settings

timeout = Settings.REQUEST_TIMEOUT
model   = Settings.LLM_PRIMARY_MODEL
api_url = f"http://{Settings.API_HOST}:{Settings.API_PORT}"
```

---

### ❌ Importing directly from internal modules
```python
# FORBIDDEN — breaks the single export point contract
from src.config.settings import Settings
from src.config.paths import PROJECT_ROOT
from src.config.dotenv import load_dotenv
```
```python
# ✅ CORRECT — always import from the package root
from src.config import Settings, PROJECT_ROOT, load_dotenv
```

---

### ❌ Re-reading .env manually
```python
# FORBIDDEN — dotenv is already loaded by config/__init__.py
import os
from dotenv import load_dotenv
load_dotenv(".env")
api_key = os.environ.get("API_KEY")
```
```python
# ✅ CORRECT — access through Settings
from src.config import Settings
api_key = Settings.LLM_API_KEY
```

---

### ❌ Constructing paths without Settings
```python
# FORBIDDEN — path doesn't adapt to environment
log_path = "logs/cv_generator.log"
cache_path = Path.home() / ".cache" / "chaincv"
```
```python
# ✅ CORRECT — paths flow from Settings which resolves against PROJECT_ROOT
from src.config import Settings, setup_logger
logger = setup_logger(Settings.LOG_DIR / "service.log", name="chaincv.services.cv_generator")
```

---

### ❌ Adding project-specific fields to the generic template
```python
# FORBIDDEN — never modify the copied config/ template directly
# src/config/settings.py:
class Settings(BaseSettings):
    SOLANA_RPC_URL: str = "https://api.mainnet-beta.solana.com"  # ← project-specific!
```
```python
# ✅ CORRECT — extend Settings in a project-specific layer or add directly to
# your project's src/config/settings.py (which is the project copy, not the template)
class Settings(BaseSettings):
    # Generic base fields ...

    # ChainCV-specific fields
    SOLANA_RPC_URL: str = Field(default="https://api.mainnet-beta.solana.com", validation_alias="SOLANA_RPC_URL")
    ARWEAVE_GATEWAY: str = Field(default="https://arweave.net", validation_alias="ARWEAVE_GATEWAY")
    MINT_FEE_SOL: float = Field(default=0.002, validation_alias="MINT_FEE_SOL")
```

---

### Settings Enforcement Checklist

- [ ] No hardcoded URLs, ports, model names, timeouts, or paths in any module
- [ ] No `import os; os.environ.get(...)` outside `config/dotenv.py`
- [ ] No `from src.config.settings import Settings` — only `from src.config import Settings`
- [ ] Every new configurable value is a field in `Settings`, not a module-level constant
- [ ] `.env` keys are documented in `.env.example`

---

## Part 2 — Logger Usage Rules

`setup_logger()` creates a **rotating file + console logger** with a standardized format. Every module gets exactly one logger, defined at module level. All scripts within the same directory (layer) must share the same log file named after the layer (e.g., `service.log`, `router.log`).

---

### ❌ Using print() for runtime output
```python
# FORBIDDEN — print() is invisible in production and has no severity level
print(f"Processing section: {section_id}")
print("CV generated successfully")
print(f"ERROR: Failed to load {format_id}")
```
```python
# ✅ CORRECT — use the module logger
logger.info(f"CV generated for format='{format_id}'")
logger.debug(f"Processing section: {section_id}")
logger.error(f"Failed to load format '{format_id}': {e}")
```

---

### ❌ Creating loggers without setup_logger
```python
# FORBIDDEN — bypasses rotating file handler and standardized format
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(format="%(message)s")

# Also forbidden — local handler setup
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
```
```python
# ✅ CORRECT — always use setup_logger from config
from src.config import setup_logger, Settings

logger = setup_logger(
    Settings.LOG_DIR / "service.log",
    name="chaincv.services.cv_generator"
)
```

---

### ❌ One logger shared across modules
```python
# FORBIDDEN — importing another module's logger
from src.services.cv_generator import logger   # ← stealing another module's logger

# Also forbidden — generic unnamed logger
logger = setup_logger(Settings.LOG_DIR / "app.log")  # no name = root logger pollution
```
```python
# ✅ CORRECT — each module owns its own named logger
# src/services/cv_generator.py
logger = setup_logger(Settings.LOG_DIR / "service.log", name="chaincv.services.cv_generator")

# src/services/cv_library.py
logger = setup_logger(Settings.LOG_DIR / "service.log", name="chaincv.services.cv_library")

# src/routers/generator.py
logger = setup_logger(Settings.LOG_DIR / "router.log", name="chaincv.routers.generator")
```

---

### ❌ Wrong log level usage
```python
# FORBIDDEN — wrong severity signals
logger.error("Starting CV generation...")         # error for a normal event
logger.info(f"Failed to load theme: {e}")         # info for an actual error
logger.warning("CV generated successfully")       # warning for a success
logger.debug(f"Critical auth failure: {e}")       # debug hides critical issues
```
```python
# ✅ CORRECT — match level to actual severity
logger.debug("Resolved component: header/clocks/terminal_clock")  # dev tracing
logger.info("CV generated successfully for format='cyberpunk'")   # normal operations
logger.warning("Theme 'neon' not found, falling back to default") # recoverable issues
logger.error(f"Failed to parse format '{format_id}': {e}")        # caught exception
```

---

### Logger Naming Convention

```
chaincv.{layer}.{module_name}

Examples:
  chaincv.services.cv_generator
  chaincv.services.cv_library
  chaincv.services.cv_editor
  chaincv.routers.generator
  chaincv.routers.editor
  chaincv.providers.solana
  chaincv.providers.arweave
  chaincv.core.renderer
```

> This naming hierarchy lets you filter logs by layer in production:
> `grep "chaincv.services" app.log` shows only service-layer events.

---

### Logger Module Template

```python
# Every service/router/provider/core module starts with this pattern:

from src.config import setup_logger, Settings

logger = setup_logger(
    Settings.LOG_DIR / "{layer}.log",
    name="chaincv.{layer}.{module_name}"
)

# Then use:
# logger.debug(...)   — dev tracing, disabled in production
# logger.info(...)    — normal operations
# logger.warning(...) — recoverable issues
# logger.error(...)   — caught exceptions (always include the exception: {e})
```

---

### Logger Enforcement Checklist

- [ ] `print()` **does NOT appear** in any service, router, core, provider, or plugin
- [ ] Every module has exactly **one** `logger = setup_logger(...)` at module level
- [ ] Logger `name` follows `"chaincv.{layer}.{module}"` convention
- [ ] `logger.error(...)` always includes the exception variable: `f"...: {e}"`
- [ ] `logging.basicConfig(...)` **does NOT appear** anywhere in the project
- [ ] No module imports another module's `logger`
