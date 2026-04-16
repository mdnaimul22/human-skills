---
name: "directory-structure"
description: "Generate a professional ASCII directory structure in Markdown. Use this before modifying a project to understand its layout, identify key files, visualize or document the file structure of a directory, project or codebase."
version: "1.0.0"
author: "Human Skill Team"
tags: ["documentation", "structure", "visualization", "tree", "file-system"]
trigger_patterns:
  - "directory structure"
  - "file tree"
  - "show structure"
  - "visualize folder"
  - "project structure"
  - "codebase tree"
  - "list files"
  - "dir structure"
---

# Directory Structure Generator

## When to Use

Activate this skill when the user asks to:
- Understand the directory structure of a project
- Show the directory structure of a project
- Visualize the file tree of a codebase
- Document the folder organization
- List files in a structured format
- Generate a markdown representation of a directory

## The **tree_gen** Tool

This skill uses the `tree_gen` tool to create Markdown-formatted directory trees.

### 📝 PARAMETERS:
- `input_path`: **REQUIRED** - Absolute path of the directory to scan.
- `output_path`: *OPTIONAL* - Where to write the output file. Defaults to `input_path`.
- `file_name`: *OPTIONAL* - Output filename. Defaults to `{dir_name}_structure.md`.
- `layout`: *OPTIONAL* - `"vertical"` (default, classic top-down) or `"horizontal"` (top-level dirs side-by-side).
- `max_depth`: *OPTIONAL* - How many levels deep to recurse. Default: `4`. Set `0` for unlimited.
- `use_gitignore`: *OPTIONAL* - Read and apply `.gitignore` rules. Default: `true`.
- `ignored_path`: *OPTIONAL* - Comma-separated absolute paths to exclude.
- `ignored_extensions`: *OPTIONAL* - Comma-separated extensions to exclude (e.g. `.log,.tmp`).


## Decision Tree: How to Use This Tool

### 1️⃣ Identify the Scope

**Ask yourself:**
- Is this a small project (<100 files)?
- Is this a large codebase (>1000 files)?
- Does the user want the full project or a specific folder?
- Do they want all files or just source code?

### 2️⃣ Choose the Right Strategy

| Scenario | Strategy |
|----------|----------|
| **Small project** | Scan everything, minimal ignores |
| **Medium web app** | Ignore node_modules, build outputs |
| **Large monorepo** | Target specific directories, aggressive ignores |
| **Root-level scan** | Always ignore knowledge, chats, workdir |
| **Source code only** | Ignore all non-code files |

---

### 📋 USAGE EXAMPLES:

#### 1. Full example:
This is a full agument example for a deep map of tha project. where you are excluding tests/ and docs/ to keep it focused using a custom filename and vertical layout.

python scripts/tree_gen.py --max_depth 3 --use_gitignore true --layout vertical --file_name PROJECT_MAP --input_path home/usr/projects/my-project/ --output_path home/usr/projects/my-project/ --ignored_path home/usr/projects/my-project/tests, home/usr/projects/my-project/docs --ignored_extensions .csv,.json

```json
{
    "tool_name": "tree_gen",
    "tool_args": { 
        "max_depth":          6,
        "use_gitignore":      "true",
        "layout":             "vertical",
        "file_name":          "PROJECT_MAP",
        "input_path":         "home/usr/projects/my-project/",
        "output_path":        "home/usr/projects/my-project/",
        "ignored_path":       "home/usr/projects/my-project/tests, home/usr/projects/my-project/docs",
        "ignored_extensions": ".csv,.json"
    }
}
```

### ⚠️ IMPORTANT NOTES:
- Common patterns (`.git`, `node_modules`, `__pycache__`, binaries, media) are auto-ignored.
- If output exceeds 500 lines, a tip is shown to reduce `max_depth` or add `ignored_path`.
- Default filename: `{dir_name}_structure.md` (e.g. `core_structure.md`).

## Scenario-Based Instructions

### 📁 Scenario 1: Small Project (< 100 files)

**When:** User has a simple script, small library, or personal project

**What to ignore:** Minimal - only critical clutter
- `__pycache__`, `.git`, `.venv`, `node_modules`

**Example:**
```json
{
    "thoughts": [
        "Small Python project, will show almost everything",
        "Only ignoring Python cache and git files",
        "Using default depth of 4"
    ],
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr/workdir/my-folder",
        "ignored_path": "__pycache__, .git, .venv, .env, .gitkeep, .DS_Store, .log, .tmp"
    }
}
```

---

### 📦 Scenario 2: Medium Web Application (100–1000 files)

**When:** Typical React/Vue/Node.js app with dependencies

**What to ignore:** Dependencies and build artifacts
- `node_modules`, `dist`, `build`, `coverage`
- `.next`, `.nuxt`, `.cache`
- `__pycache__`, `.pytest_cache`

**Example:**
```json
{
    "thoughts": [
        "Medium-sized Next.js app",
        "Ignoring dependencies and build outputs for cleaner view"
    ],
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr/workdir/my-webapp",
        "ignored_path": "node_modules, dist, .next, coverage, __pycache__, .git, .venv, .env, .gitkeep, .DS_Store, .log, .tmp"
    }
}
```

---

### 🏢 Scenario 3: Large Codebase/Monorepo (> 1000 files)

**When:** Enterprise application, monorepo, or complex system

**Strategy:** 
1. **Never scan the entire root** - it will be too large
2. **Target specific packages/modules** one at a time
3. **Use aggressive ignores**

**What to ignore:** Everything non-essential
- All dependencies: `node_modules`, `vendor`, `.venv`
- All build outputs: `dist`, `build`, `out`, `target`
- All test files and coverage
- All media and assets

**Example - Scan specific package:**
```json
{
    "thoughts": [
        "Large monorepo - targeting only the backend package",
        "Ignoring tests and dependencies for manageable output"
    ],
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr/workdir/monorepo/packages/backend",
        "ignored_path": "node_modules, dist, coverage, tests, __tests__, .git"
    }
}
```

**Example - Multiple targeted scans:**
```json
// First: Backend
{
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr/workdir/monorepo/packages/backend",
        "output_path": "/a0/usr/workdir/docs",
        "ignored_path": "node_modules, dist, tests"
    }
}

// Then: Frontend (separate call)
{
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr/workdir/monorepo/packages/frontend",
        "output_path": "/a0/usr/workdir/docs",
        "ignored_path": "node_modules, .next, public/assets"
    }
}
```

---

### 🌍 Scenario 4: Root-Level Scan (/a0/usr or system root)

**When:** User wants to see the entire workspace or system structure

**⚠️ CRITICAL RULES:**
1. **ALWAYS ignore these paths for /a0/usr:**
   - `/a0/usr/workdir` (user projects - scan separately)
   - `/a0/usr/chats` (conversation history)
   - `/a0/usr/knowledge/main` (large knowledge base)
   - `/a0/usr/memory/default` (vector database)

2. **What to show:**
   - Agent configurations
   - Skills
   - System configuration files
   - Project metadata

**Example:**
```json
{
    "thoughts": [
        "User wants to see system structure",
        "Must ignore workdir, chats, and knowledge - they're huge"
    ],
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr",
        "ignored_path": "/a0/usr/workdir, /a0/usr/chats, /a0/usr/knowledge/main, /a0/usr/memory/default"
    }
}
```

---

### 🎯 Scenario 5: Specific Folder Deep Dive

**When:** User wants detailed view of ONE specific directory (e.g., "show me the src folder structure")

**Strategy:**
- Target ONLY that folder
- Show everything inside (minimal ignores)
- Good for code review, onboarding, documentation

**What to ignore:** Only cache and temporary files
- `__pycache__`, `.pytest_cache`
- `*.pyc`, `.DS_Store`

**Example:**
```json
{
    "thoughts": [
        "User wants detailed view of src directory",
        "Will show all source files with minimal filtering"
    ],
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr/workdir/my-app/src",
        "ignored_path": "__pycache__, .pytest_cache"
    }
}
```

---

### 📝 Scenario 6: Documentation Purpose

**When:** Creating README, docs, or architectural diagrams

**Strategy:**
- Focus on source code and configuration
- Ignore everything that's not essential to understanding
- Keep output clean and professional

**What to ignore:**
- All dependencies and node_modules
- All build outputs and artifacts
- All test files (unless specifically asked)
- All media and binary files
- All local development files (.env, .vscode)

**Example:**
```json
{
    "thoughts": [
        "Generating structure for project README",
        "Showing only source code and config, no tests or builds"
    ],
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/a0/usr/workdir/my-project",
        "output_path": "/a0/usr/workdir/my-project/docs",
        "ignored_path": "node_modules, dist, build, tests, __tests__, coverage, .git, .vscode, public/images"
    }
}
```

---

## Quick Reference: Common Ignore Patterns

### By Language/Framework

**Python Projects:**
```
__pycache__, .pytest_cache, .venv, .mypy_cache, *.pyc, dist, build
```

**Node.js Projects:**
```
node_modules, dist, build, .next, .nuxt, coverage, .cache
```

**Full-Stack Projects:**
```
node_modules, __pycache__, dist, build, .venv, coverage, .git
```

### By Purpose

**Code Review (show source only):**
```
node_modules, dist, build, tests, __tests__, coverage, docs, public
```

**Documentation (clean view):**
```
node_modules, dist, .git, .vscode, tests, coverage, *.min.js, assets
```

**Deployment Check (show build outputs):**
```
node_modules, .git, src, tests (only ignore source and development files)
```

---

## Best Practices

### ✅ DO:
1. **Always check project size first** - use `list_dir` to estimate
2. **For large projects, scan specific directories** - never scan massive roots
3. **For /a0/usr, ALWAYS ignore workdir and chats**
4. **Match ignores to user's intent** - code review vs documentation needs different ignores
5. **Present the output** - read structure.md and show it to user after generation

### ❌ DON'T:
1. **Don't scan /a0/usr/workdir directly** - ask which project inside it
2. **Don't forget node_modules** - it can have 100k+ files
3. **Don't ignore too little** - output will be overwhelming
4. **Don't use relative paths in ignored_path** - always use absolute paths
5. **Don't generate without understanding user's goal** - ask if unclear

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Output is 10,000+ lines" | Add more aggressive ignores or target smaller directory |
| "Empty structure.md" | Path doesn't exist or all files were ignored |
| "Still showing node_modules" | Use absolute path: `/full/path/to/node_modules` |
| "Missing important files" | Review ignored_path - may have over-filtered |

## Troubleshooting

### Issue: Empty Output

**Cause:** Directory doesn't exist or is empty.
**Solution:** Verify the path exists with `list_dir` first.

### Issue: Too Much Output

**Cause:** Not enough ignore patterns.
**Solution:** Add more paths/extensions to ignore, or generate subdirectories separately.

### Issue: File Not Found

**Cause:** Output directory doesn't exist.
**Solution:** Create output directory first or use existing path.

## Output Format

The generated `structure.md` file contains:
- Markdown-formatted tree structure
- File and folder counts
- List of ignored paths/patterns
- Generation timestamp

Example output:
```markdown
## file tree
/my-project/
├── src/
│   ├── main.py
│   └── utils/
│       └── helpers.py
├── tests/
│   └── test_main.py
└── README.md
```

## Related Skills

- **file-analysis** - For detailed file content analysis
- **code-review** - For examining code structure and quality
- **documentation** - For generating comprehensive project docs