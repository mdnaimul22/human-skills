---
name: architecture-auditing-linter
description: Ensure every project remains compliant with these standards, use the built-in `linter` tool. It scans codebase for violations of the architecture rules using AST parsing.
---

# Architecture Auditing (Linter)
> *"Trust, but verify."*

It scans your code for violations of the architecture rules for logging, pathlib, print, etc. 

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
