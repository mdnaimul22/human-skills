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
curl -sSL https://raw.githubusercontent.com/mdnaimul22/human-skills/main/skills/scaffold-project/resources/initialize/bootstrap.py | python3
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
│   └── project-tree-example.md
└── src/
    ├── __init__.py
    ├── requirements.txt
    ├── config/              ← [scaffold-config] Settings, env, file I/O, logger
    ├── helpers/             ← [scaffold-helpers] Exceptions, retry, middleware, DB
    ├── core/
    ├── providers/
    ├── schema/
    ├── services/
    └── routers/
```

## main.py Features

The generated `main.py` includes:

1. **FastAPI app** with lifespan (startup/shutdown hooks)
2. **Logger** initialized via `setup_logger`
3. **CORS, Middleware, Error Handlers** auto-registered from `src/helpers`
4. **Database** hooks (commented out, uncomment when needed)
5. **Health check** endpoint at `/health`
6. **Auto-kill switch** — `kill_pid(port)` frees the port before starting

> [!CAUTION]
> **Never remove `kill_pid(port)` from main.py!**
> This function auto-kills any orphaned server process holding the port before startup. Without it, you'll get `Address already in use` errors.

---

## Post-Bootstrap Checklist

- [ ] Copy `.env.example` → `.env` and fill mandatory fields
- [ ] Add project-specific fields to `src/config/settings.py`
- [ ] Rename `AppError` in `exceptions.py` to your project name (optional)
- [ ] Add dependencies to `pyproject.toml` (e.g. `tenacity`, `fastapi`, `sqlalchemy[asyncio]`)
- [ ] ⚠️ Never remove `kill_pid(port)` from `main.py`

---

## Related Skills

| Skill | Purpose |
|:---|:---|
| `scaffold-config` | Scaffold `src/config/` layer standalone |
| `scaffold-helpers` | Scaffold `src/helpers/` layer standalone |
| `scaffold-ui` | Scaffold `web/` frontend layer |
