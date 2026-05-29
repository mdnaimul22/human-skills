
# Helpers Usage Rules

> **`src/helpers/` is the single source of truth for exceptions, retry logic, date utilities, port management, and database access.**
> Never re-implement what helpers already provides.

---

## Part 1 — Exception Hierarchy

`src/helpers/exceptions.py` provides a **complete HTTP-mapped exception hierarchy**. Every error in services, core, and providers must use these classes — never raise raw `Exception` or `ValueError` for business logic errors.

---

### ❌ Raising raw exceptions for business errors
```python
# FORBIDDEN — raw exceptions bypass error handlers and leak stack traces
raise Exception("User not found")
raise ValueError("Invalid email format")
raise RuntimeError("Payment service failed")
```
```python
# ✅ CORRECT — use the typed exception hierarchy
from src.helpers import NotFoundError, ValidationError, ExternalServiceError

raise NotFoundError("User", user_id)              # → 404
raise ValidationError("Invalid email format")      # → 400
raise ExternalServiceError("Stripe", "declined")   # → 502
```

---

### ❌ Generic catch-all without AppError awareness
```python
# FORBIDDEN — swallows errors silently, no structured response
try:
    result = process_order(order_id)
except Exception:
    return {"error": "Something went wrong"}
```
```python
# ✅ CORRECT — catch specific AppError subclasses, let others propagate
from src.helpers import NotFoundError, AppError

try:
    result = process_order(order_id)
except NotFoundError:
    raise  # Let global error handler return proper 404
except AppError:
    raise  # Let global error handler return proper status
# Unhandled exceptions → catch-all handler returns 500 automatically
```

---

### Complete Exception Reference

| Exception | Status | When to Use |
|:---|:---|:---|
| `NotFoundError(resource, id)` | 404 | Resource lookup returned None |
| `ValidationError(message)` | 400 | Input validation failure |
| `ExternalServiceError(service, msg)` | 502 | Third-party API failure |
| `PermissionDeniedError(message)` | 403 | Authorization failure |
| `ConflictError(message)` | 409 | Duplicate or state conflict |
| `RateLimitError(message, retry_after)` | 429 | Too many requests |

---

## Part 2 — Retry Logic

`src/helpers/retry.py` provides **production-grade retry with exponential backoff + jitter** via Tenacity. Never write manual retry loops.

---

### ❌ Manual retry loops
```python
# FORBIDDEN — no backoff, no jitter, blocks thread, no error classification
import time

for attempt in range(3):
    try:
        response = requests.get(url, timeout=10)
        break
    except Exception:
        time.sleep(2)
```
```python
# ✅ CORRECT — decorator with exponential backoff + jitter
from src.helpers import retry_on_failure

@retry_on_failure(max_attempts=3)
def fetch_data():
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

---

### ❌ Manual async retry
```python
# FORBIDDEN
retries = 0
while retries < 5:
    try:
        result = await client.get(url)
        break
    except Exception:
        retries += 1
        await asyncio.sleep(retries * 2)
```
```python
# ✅ CORRECT — async decorator
from src.helpers import retry_async_on_failure

@retry_async_on_failure(max_attempts=5, retryable=(ConnectionError, TimeoutError))
async def fetch_data():
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
```

---

## Part 3 — Date & Time Utilities

`src/helpers/date_utils.py` provides **standardized ISO 8601 timestamps** (UTC). Never use raw `datetime` formatting.

---

### ❌ Raw datetime formatting
```python
# FORBIDDEN — inconsistent formats, timezone-naive, scattered patterns
from datetime import datetime

timestamp = datetime.now().isoformat()
timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
timestamp = str(datetime.now())
```
```python
# ✅ CORRECT — always UTC, always ISO 8601
from src.helpers import get_now_iso, parse_iso, relative_time

timestamp = get_now_iso()                  # "2025-05-15T14:30:00+00:00"
dt = parse_iso("2025-05-15T14:30:00")     # datetime (UTC-aware)
ago = relative_time(some_datetime)          # "2 hours ago"
```

---

## Part 4 — Port Management

`src/helpers/port_utils.py` handles **orphaned server process cleanup**. Never write raw subprocess port-killing.

---

### ❌ Manual port killing
```python
# FORBIDDEN — fragile, no fallback, no logging
import subprocess
subprocess.run(["kill", "-9", str(pid)])
subprocess.run(["fuser", "-k", "8000/tcp"])
```
```python
# ✅ CORRECT — graceful SIGTERM → SIGKILL fallback with logging
from src.helpers import kill_pid, get_pid

kill_pid(8000)     # Gracefully frees port 8000
pids = get_pid(8000)  # Check what's holding the port
```

---

## Part 5 — Database Layer (Optional)

If SQLAlchemy is installed, `connection.py` and `repository.py` provide an **async database layer** with session management and generic CRUD.

---

### ❌ Manual SQLAlchemy boilerplate
```python
# FORBIDDEN — scattered engine creation, no session management
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///app.db")
async_session = sessionmaker(engine, class_=AsyncSession)
```
```python
# ✅ CORRECT — centralized lifecycle
from src.helpers import init_db, get_session, shutdown_db, BaseRepository

# In main.py lifespan:
init_db(Settings.DATABASE_URL)
# yield
await shutdown_db()

# In routers (dependency injection):
async def get_users(session: AsyncSession = Depends(get_session)):
    repo = UserRepository(session)
    return await repo.list()
```

---

### ❌ Repeated CRUD logic per model
```python
# FORBIDDEN — copy-paste CRUD in every repository
async def get_user(session, user_id):
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(session, **data):
    user = User(**data)
    session.add(user)
    await session.commit()
    return user
```
```python
# ✅ CORRECT — extend BaseRepository
from src.helpers import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)

    # Custom queries only:
    async def find_by_email(self, email: str) -> User | None:
        stmt = select(self.model).where(self.model.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

---

## Enforcement Checklist

Before every commit, verify in any file you touch:

- [ ] No raw `raise Exception(...)` or `raise ValueError(...)` for business logic
- [ ] All business errors use `AppError` subclasses from `src.helpers`
- [ ] No manual `for/while` retry loops — use `@retry_on_failure`
- [ ] No raw `datetime.now().isoformat()` — use `get_now_iso()`
- [ ] No raw `subprocess` for port killing — use `kill_pid()`
- [ ] No scattered `create_async_engine()` — use `init_db()` from helpers
- [ ] No copy-paste CRUD — extend `BaseRepository`
