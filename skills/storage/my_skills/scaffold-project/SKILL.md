---
name: scaffold-project
description: Bootstraps a complete Python project skeleton — directories, config layer, helpers, rules, and a FastAPI-ready main.py. One command, zero boilerplate.
---

# Scaffold Project
> *"One command. Full project skeleton."*

Initializes a complete, production-ready Python project from scratch — directories, config layer, helpers layer, agent rules, and a FastAPI-ready `main.py` entry point.

## How to Use

### Via `human-skills` CLI
```bash
human-skills '{
    "tool_name": "bootstrap",
    "tool_args": {
        "destination": "/path/to/new_project"
    }
}'
```

### Via `curl` (no dependencies)
```bash
curl -sSL https://raw.githubusercontent.com/mdnaimul22/human-skills/main/skills/storage/my_skills/scaffold-project/resources/initialize/bootstrap.py | python3
```

---

## What Bootstrap Creates

```
project_root/
├── main.py                  ← FastAPI entry point with auto-kill, health check, lifespan
├── .env                     ← Environment variables (fill from .env.example)
├── .env.example             ← Template for required env vars
├── .gitignore               ← Pre-configured for Python projects
├── README.md
├── LICENSE                  ← MIT License
├── docs/
├── logs/
├── tests/
│   └── __init__.py
├── .agents/rules/           ← Coding standards synced from human-skills
│   ├── coding-standards.md
│   ├── architecture-patterns.md
│   ├── maintenance-testing.md
│   ├── config-path-rules.md
│   ├── config-usage-rules.md
│   ├── helpers-usage-rules.md
│   ├── project-config-example.md
│   ├── project-tree-example.md
│   └── common-git-workflow.md
└── src/
    ├── __init__.py
    ├── requirements.txt
    ├── config/              ← [scaffold-config] Settings, env, file I/O, logger
    ├── db/                  ← [Built-in] Connection, base repository, models, repositories
    ├── helpers/             ← [Built-in] Exceptions, retry, middleware, port utils
    ├── core/                ← [Built-in] Pure business logic (auth, tokens, crypto)
    ├── providers/           ← [Built-in] External service integrations (Email, Google, Tailscale)
    ├── schema/              ← [Built-in] Pydantic data contracts
    ├── services/            ← [Built-in] Use-case orchestration (Core + Providers + DB)
    └── routers/             ← [Built-in] HTTP API endpoints & dependencies
```

## Built-in Auth System

The scaffold ships with a **production-grade authentication system** out of the box:

### Auth Endpoints

| Method | Endpoint | Auth | Purpose |
|:---|:---|:---|:---|
| `POST` | `/api/auth/register` | ❌ | Email signup → sends verification email |
| `GET` | `/api/auth/verify-email` | ❌ | Verify email via token in query |
| `POST` | `/api/auth/login` | ❌ | Email/password login → access + refresh tokens |
| `POST` | `/api/auth/google` | ❌ | Google OAuth login/signup |
| `POST` | `/api/auth/refresh` | ❌ | Rotate access + refresh tokens |
| `POST` | `/api/auth/forgot-password` | ❌ | Request password reset email |
| `POST` | `/api/auth/reset-password` | ❌ | Reset password with token |
| `POST` | `/api/auth/change-password` | ✅ | Change password (authenticated) |
| `GET` | `/api/auth/me` | ✅ | Get current user profile |
| `PATCH` | `/api/auth/me` | ✅ | Update profile (name) |
| `POST` | `/api/auth/logout` | ✅ | Client-side token clear guidance |

### JWT Token Design

Purpose-scoped tokens prevent cross-purpose token abuse:

| Purpose | Expiry | Usage |
|:---|:---|:---|
| `access` | 15 minutes | API Authorization header |
| `refresh` | 7 days | POST /refresh only |
| `verify_email` | 24 hours | Email verification link |
| `reset_password` | 1 hour | Password reset link |

### User ↔ Service Data Ownership

Use `OwnershipMixin` for any model that belongs to a user:

```python
from src.db import Base, TimestampMixin, OwnershipMixin

class Post(Base, TimestampMixin, OwnershipMixin):
    __tablename__ = "posts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
```

`BaseRepository` provides `list_by_owner(user_id)` and `count_by_owner(user_id)` for scoped queries.

### Google OAuth Setup (Optional)

1. Set `GOOGLE_CLIENT_ID` in `.env`
2. Install: `pip install google-auth` (or `pip install .[google]`)
3. Frontend sends Google ID token → `POST /api/auth/google`

If `GOOGLE_CLIENT_ID` is not set, the endpoint returns a clear error.

---

## main.py Features

The generated `main.py` includes:

1. **FastAPI app** with lifespan (startup/shutdown hooks)
2. **Logger** initialized via `setup_logger`
3. **CORS, Middleware, Error Handlers** auto-registered from `src/helpers`
4. **Database** hooks (init + create_tables on startup, shutdown on exit)
5. **Health check** endpoint at `/health`
6. **Auto-kill switch** — `kill_pid(port)` frees the port before starting

> [!CAUTION]
> **Never remove `kill_pid(port)` from main.py!**
> This function auto-kills any orphaned server process holding the port before startup. Without it, you'll get `Address already in use` errors.

---

## Post-Bootstrap Checklist

- [ ] Copy `.env.example` → `.env` and fill mandatory fields
- [ ] Add project-specific fields to `src/config/settings.py`
- [ ] Set `JWT_SECRET` to a strong random value for production
- [ ] Configure SMTP settings for email verification/password reset
- [ ] (Optional) Set `GOOGLE_CLIENT_ID` for Google OAuth
- [ ] Rename `AppError` in `exceptions.py` to your project name (optional)
- [ ] Add dependencies to `pyproject.toml`
- [ ] ⚠️ Never remove `kill_pid(port)` from `main.py`

---

## Related Skills

| Skill | Purpose |
|:---|:---|
| `scaffold-config` | Scaffold `src/config/` layer standalone |
| `scaffold-ui` | Scaffold `web/` frontend layer |
