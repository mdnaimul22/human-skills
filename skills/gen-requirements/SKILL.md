---
name: gen-requirements
description: Auto-generates clean, categorized requirements.txt and PEP 621 pyproject.toml by scanning Python codebase imports via AST. Resolves PyPI package names and installed versions.
version: 1.0.0
author: Human Skill Team
tags: ["python", "dependencies", "requirements", "pyproject", "ast", "scaffold"]
trigger_patterns:
  - "generate requirements"
  - "create requirements.txt"
  - "generate pyproject.toml"
  - "scan dependencies"
  - "auto requirements"
  - "pip requirements"
---

# Requirements & Dependency Generator

> *"One command. Zero manual dependency hunting."*

Auto-generates clean, categorized `requirements.txt` and PEP 621-compliant `pyproject.toml` files by analyzing Python codebase imports using Abstract Syntax Trees (AST).

---

## When to Use

Activate this skill when:
- Creating or updating `requirements.txt` for a Python project
- Generating PEP 621 `pyproject.toml` with dependencies and dev-dependencies
- Scanning a codebase to identify missing or used third-party packages
- Preparing a project for production deployment or distribution

---

## How to Use

### Via `human-skills` CLI

#### 1. Standard Generation (Minimum Constraints `>=X.Y.0`)
```bash
human-skills '{
    "tool_name": "gen_requirements",
    "tool_args": {
        "path": "/path/to/your/project"
    }
}'
```

#### 2. Exact Pinned Versions (`==X.Y.Z`)
```bash
human-skills '{
    "tool_name": "gen_requirements",
    "tool_args": {
        "path": "/path/to/your/project",
        "exact": "true"
    }
}'
```

#### 3. Custom Output Directory and Project Name
```bash
human-skills '{
    "tool_name": "gen_requirements",
    "tool_args": {
        "path": "/path/to/your/project",
        "name": "my-awesome-app",
        "output_dir": "/path/to/your/project"
    }
}'
```

#### 4. Specific Output Format
```bash
# Only requirements.txt
human-skills '{
    "tool_name": "gen_requirements",
    "tool_args": {
        "path": "/path/to/your/project",
        "format": "requirements"
    }
}'

# Only pyproject.toml
human-skills '{
    "tool_name": "gen_requirements",
    "tool_args": {
        "path": "/path/to/your/project",
        "format": "pyproject"
    }
}'
```

---

## Parameters

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `path` | string | No | `.` | Target Python project root directory to scan. |
| `exact` | string | No | `"false"` | Use exact pinned versions (`==X.Y.Z`) if `"true"`, otherwise `>=X.Y.0`. |
| `name` | string | No | Dir name | Project name written in `pyproject.toml`. |
| `output_dir` | string | No | `path` | Output directory where files will be created. |
| `format` | string | No | `"both"` | Output format: `"both"`, `"requirements"`, or `"pyproject"`. |

---

## Key Features

1. **AST-Powered Inspection:** Parses actual abstract syntax trees (`import x`, `from y import z`) without executing code.
2. **Standard Library Filtering:** Automatically ignores all Python standard library modules (`os`, `sys`, `json`, `asyncio`, `pathlib`, etc.).
3. **Local Module Isolation:** Intelligently detects internal project packages (`src`, `helpers`, `config`, local scripts) to prevent false-positive dependencies.
4. **PyPI Distribution Mapping:** Accurately maps non-trivial import names to their actual PyPI package names (e.g. `cv2` → `opencv-python`, `PIL` → `pillow`, `pydantic_settings` → `pydantic-settings`).
5. **Functional Categorization:** Groups packages in `requirements.txt` by role (Core Math, Web/Networking, AI/Deep Learning, Configuration, Testing, etc.).
6. **PEP 621 Standard:** Outputs standard `pyproject.toml` with separate `dependencies` and `[project.optional-dependencies] dev`.
