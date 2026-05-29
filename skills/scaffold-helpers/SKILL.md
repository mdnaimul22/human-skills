---
name: scaffold-helpers
description: Scaffolds battle-tested helper modules — exception hierarchy, retry logic, date utilities, port management, FastAPI middleware, and async database layer.
---

# Scaffold Helpers
> *"Universal utilities, zero boilerplate."*

Scaffolds battle-tested helper modules that every Python project needs. These are **framework-agnostic** — they work identically in FastAPI, Flask, CLI tools, or background workers.

## How to Use

### Fresh project (safe mode — only adds new files)
```bash
human-skills '{
    "tool_name": "sethelpers",
    "tool_args": {
        "destination": "/path/to/your_project/src/helpers"
    }
}'
```

### Force overwrite matching files only
```bash
human-skills '{
    "tool_name": "sethelpers",
    "tool_args": {
        "destination": "/path/to/your_project/src/helpers",
        "override": "true"
    }
}'
```

---

## Helpers Structure

```
helpers/
├── __init__.py       ← Single export point with graceful degradation
├── exceptions.py     ← AppError → NotFoundError, ValidationError, etc.
├── date_utils.py     ← ISO 8601, timezone-aware parsing, relative time
├── retry.py          ← Tenacity-based exponential backoff (sync + async)
├── port_utils.py     ← Auto-kill orphaned server processes
├── cors.py           ← [Optional] CORS configuration (requires FastAPI)
├── middleware.py     ← [Optional] Request logging middleware (requires FastAPI)
├── error_handlers.py ← [Optional] Global exception handlers (requires FastAPI)
├── connection.py     ← [Optional] Async database engine (requires SQLAlchemy)
└── repository.py     ← [Optional] Base CRUD repository (requires SQLAlchemy)
```

---

## API Quick Reference

### Exceptions (`always available`)
```python
from src.helpers import NotFoundError, ValidationError, ExternalServiceError

raise NotFoundError("User", user_id)              # → 404
raise ValidationError("Invalid email")             # → 400
raise ExternalServiceError("Stripe", "declined")   # → 502
raise PermissionDeniedError()                       # → 403
raise ConflictError("Duplicate entry")              # → 409
raise RateLimitError(retry_after=60)                # → 429
```

### Date Utils (`always available`)
```python
from src.helpers import get_now_iso, parse_iso, relative_time

timestamp = get_now_iso()                  # "2025-05-15T14:30:00+00:00"
dt = parse_iso("2025-05-15T14:30:00")     # datetime object (UTC)
ago = relative_time(some_datetime)          # "2 hours ago"
```

### Retry Logic (`requires tenacity`)
```python
from src.helpers import retry_on_failure, retry_async_on_failure

@retry_on_failure(max_attempts=3)
def call_api():
    response = requests.get(url, timeout=10)
    response.raise_for_status()

@retry_async_on_failure(max_attempts=5, retryable=(ConnectionError, TimeoutError))
async def fetch_data():
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
```

### Port Utils (`always available`)
```python
from src.helpers import kill_pid, get_pid

kill_pid(8000)     # Gracefully frees port 8000
get_pid(8000)      # Returns list of PIDs on port 8000
```

### FastAPI Components (`requires fastapi`)
```python
from src.helpers import register_cors, register_middleware, register_error_handlers
```

### Database Layer (`requires sqlalchemy[asyncio]`)
```python
from src.helpers import init_db, get_session, shutdown_db, BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)
```

---

## Graceful Degradation

`helpers/__init__.py` uses **graceful degradation** for optional dependencies:

- **Core** (exceptions, date_utils, retry, port_utils) — **always available**
- **Web** (cors, middleware, error_handlers) — **only if FastAPI is installed**
- **DB** (connection, repository) — **only if SQLAlchemy is installed**

> [!IMPORTANT]
> The `try-except ImportError: pass` blocks in `__init__.py` are **intentional** and are NOT linter violations.

---

## Post-Scaffolding

1. Rename `AppError` → `YourProjectError` in `exceptions.py` (optional)
2. Add `tenacity` to dependencies: `pip install tenacity`
3. Import: `from src.helpers import AppError, NotFoundError`

## Enforcement

See `.agents/rules/helpers-usage-rules.md` for strict usage patterns. Manual retry loops and raw exceptions are **FORBIDDEN**.
