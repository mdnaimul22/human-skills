---
name: architecture-auditing-linter
description: Ensure every project remains compliant with these standards, use the built-in `linter` tool. It scans codebase for violations of the architecture rules using AST parsing.
---

# Architecture Auditing (Linter)
> *"Dont Trust, must verify."*

It scans your code for violations of the architecture rules for logging, pathlib, print, etc. 

### How to use?
The `human-skills` linter accepts numerous tool arguments for different purposes. Below, all available arguments are explained:

allowed_args = {
    "default": ["scan_path", "path", "ignored_path", "ignored_apth", "linter_type", "ignored_rules"],
    "rest_api": ["scan_path", "path", "ignored_path", "ignored_apth", "linter_type", "ignored_rules"]
}

```json
{
    "tool_name": "linter",
    "tool_args": {
        "scan_path": "Path to the project directory or a specific .py file to audit (REQUIRED).",
        "linter_type": "Linter mode: 'default' (architecture violations) or 'rest_api' (API quality score). Defaults to 'default'.",
        "ignored_path": "Comma-separated list of directory names to skip during scanning (e.g., 'venv, .git, tests').",
        "ignored_rules": "Comma-separated list of analyzer or rule names to skip (e.g., 'type_safety, kill_switch' in default mode, or 'auth, rate_limiting' in rest_api mode)."
    }
}
```

#### 1. Audit entire project 
```bash
human-skills '{
    "tool_name": "linter",
    "tool_args": {
        "linter_type": "default",
        "scan_path": "home/user_name/project/",
        "ignored_path": "venv, .git, tests, configs"
    }
}'
```

#### 2. Audit rest api endpoint 
```bash
human-skills '{
    "tool_name": "linter",
    "tool_args": {
        "linter_type": "rest_api",
        "scan_path": "home/user_name/project/",
        "ignored_path": "venv, .git, tests, configs",
        "ignored_rules": "auth, rate_limiting, caching"
    }
}'
```

#### 3. Audit a specific file
```bash
human-skills '{
    "tool_name": "linter",
    "tool_args": {
        "scan_path": "/path/to/your/project/src/services/logic.py"
    }
}'
```



### What it detects in `default` mode?
All rules in `default` mode are modularly located in `scripts/default/` and can be individually bypassed via `ignored_rules`:

| Rule File (`scripts/default/`) | Detected Violations & Advisories |
| :--- | :--- |
| `type_safety` | ❌ Dynamic reflection (`getattr`, `setattr`, `hasattr`), type branching/tautology (`isinstance`, `(..., object)`), and untyped boundaries (`Any`, `object` in variable/function annotations, explicit `cast(object)`). |
| `path_safety` | ❌ Direct `import pathlib` outside `config/`, `os.path` usages, forbidden `Path` methods, direct system `/tmp` directory usage (must use `data/tmp`), and manual dir creation (`exist_ok=True`). |
| `logging_rule` | ❌ Direct `import logging`, hardcoded log filenames in `setup_logger`, and `print()` in production code (exempted inside `test/` or `tests/` directories). |
| `env_config` | ❌ Direct `os.environ` / `os.getenv`, ⚠️ silent fallback defaults in `os.getenv`, and ⚠️ `Field(default=...)` in `settings.py`. |
| `manual_io` | ❌ Direct `open()`, `with open()`, `os.open()`, `os.read()`, `os.write()`. (Must use `read_text`/`write_text` from config). |
| `silent_exceptions` | ❌ Silent `except: pass` and ⚠️ raw built-in exceptions (`raise Exception/ValueError/...`). |
| `helpers_usage` | ⚠️ Direct `datetime.now()`, ❌ `create_async_engine()`, and ⚠️ manual retry loops (`time.sleep`/`asyncio.sleep` in loops). |
| `kill_switch` | ❌ `main.py` calling `uvicorn.run()` without `kill_pid()`. |
| `security_rule` | 🚨 OWASP/Bandit security suite: SQL/Command injection, weak crypto (`md5`/`sha1`), unsafe deserialization (`pickle`/`yaml`), hardcoded secrets/passwords, and SSL bypass. |
| `import_hygiene` | ❌ Wildcard imports (`from x import *`), ⚠️ deprecated stdlib modules, and ⚠️ unused imports. |
| `code_complexity` | ⚠️ Deep nesting depth (> 4 levels), high cyclomatic complexity (> 15), and oversized functions. |
| `code_duplication` | ❌ DRY violation: structural AST duplication between function bodies. |
| `memory_efficiency` | ⚠️ In-place string concatenation inside loops (`+=`), unneeded list comprehensions in generator functions, ❌ dictionary-like `get()`/`__getitem__()` on Pydantic models, and ⚠️ serialized `model_dump().get()` calls. |
| `clean_code` | ❌ Rule 10 compliance: docstrings (`"""..."""`) and standalone/top-level comment lines (`#`). Only essential trailing inline comments after code (`code # info`) are allowed. |
| `pythonic_standards` | ❌ PEP 8 naming (classes PascalCase, functions snake_case), shadowing Python built-ins, and `global` statement usage. |

### What it detects in `rest_api` mode?
When `linter_type="rest_api"` is used, it evaluates router files based on Enterprise API Best Practices.

> [!NOTE]
> **Why use `ignored_rules`?**
> There can be many conventions for API endpoints, but not all conventions apply to a single script. That's exactly why the ignore mechanism is kept. For example, global rules like `error_handling` (e.g., global exception handlers) or `input_validation` (e.g., file upload limits) might be handled globally in `others_script.py` and may not apply when analyzing a single local endpoint file. You should use `ignored_rules` to skip rules that are handled globally elsewhere or are irrelevant to the specific endpoint context.

| Analyzer Rule | Description | When to Ignore (`ignored_rules`) |
| :--- | :--- | :--- |
| `auth` | Checks for authentication tokens, JWT, or `@login_required` decorators. | Ignore for **Local Utilities** (e.g., desktop tools like `epic-adb` running on `127.0.0.1`) or open/public data APIs. |
| `rate_limiting` | Checks for rate limiting mechanisms to prevent abuse. | Ignore for **Local Desktop Tools** or internal microservices sitting behind an API Gateway. |
| `caching` | Checks for `Cache-Control` headers or Redis usage. | Ignore for APIs that handle **Real-time Data** (like device state or live logs) where caching causes stale data. |
| `pagination` | Checks for `limit`, `offset`, or `page` parameters. | Ignore for APIs returning small, fixed lists (e.g., categories, active local devices). |
| `retry_logic` | Checks for automated retries on API failures. | Generally useful, but can be ignored if the client-side handles retries exclusively. |
| `input_validation` | Enforces Pydantic/Marshmallow schema validation at the endpoint. | *Should rarely be ignored.* Protects against malformed data. |
| `error_handling` | Detects bare `except Exception:` and enforces specific exception handling. | *Do not ignore.* Essential for debugging. |
| `status_code` | Ensures standard HTTP status codes (200, 400, 500) are used correctly. | *Do not ignore.* |
| `n1_query` | Detects loops containing database queries (N+1 problem). | *Do not ignore.* Critical for performance. |
| `timeout` | Ensures external requests have a defined timeout to prevent hanging. | *Do not ignore.* |
| `endpoint_naming` | Enforces RESTful noun-based naming conventions (e.g., `/users` instead of `/getUsers`). | *Do not ignore.* |
| `http_method` | Ensures GET for reading, POST for creating, etc. | *Do not ignore.* |
| `request_logging` | Checks if request ID, HTTP method, and latency are logged structurely. | *Do not ignore.* Critical for observability. |
| `response_filtering` | Checks for sparse fieldsets (e.g. `?fields=`) to prevent fetching unused columns. | Can be ignored if data models are very small. |
| `sensitive_data` | Checks if sensitive fields like password or token are omitted from responses. | *Do not ignore.* |
| `idempotency` | Checks for idempotency keys on mutation endpoints. | Ignore if you are not processing financial transactions or state-critical operations. |

---
