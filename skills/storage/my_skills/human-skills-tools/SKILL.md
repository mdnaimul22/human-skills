---
name: "human-skills-tools"
description: "Core file system inspection and manipulation toolset for agents: find_by_name, grep_search, list_dir, view_file, and write_to_file."
version: "1.0.0"
author: "Human Skills Team"
tags: ["filesystem", "tools", "inspection", "search", "grep", "file-reader", "file-writer", "list-dir"]
trigger_patterns:
  - "find files"
  - "search codebase"
  - "grep search"
  - "list directory"
  - "view file"
  - "read file"
  - "write file"
  - "create file"
---

# Human Skills Tools — File System & Code Inspection Suite

> *"Fast, deterministic file system inspection and safe code manipulation tools for autonomous agents."*

---

## When to Use

Activate this skill when you need to inspect, search, traverse, read, or create files in a project workspace:
- Locate files by name or pattern across directories (`find_by_name`)
- Search code patterns, function definitions, or strings across files (`grep_search`)
- Explore folder contents, file sizes, modification times, and permissions (`list_dir`)
- Read and inspect exact source code lines with line numbering and range slicing (`view_file`)
- Safely write or overwrite files with automated syntax validation (`write_to_file`)

---

## Tool Selection Guide

| Need | Recommended Tool | Key Capabilities |
|:---|:---:|:---|
| Locate files or folders by name | `find_by_name` | Glob patterns, depth limits, directory/file filters, path exclusions |
| Search code for text, tokens, or functions | `grep_search` | AST context tagging (functions/classes), line numbers, file filters |
| Inspect directory contents and metadata | `list_dir` | Markdown table with file types, sizes, timestamps, permissions |
| Read source code or config files | `view_file` | Numbered lines, line ranges (`start_line`, `end_line`), memory caching |
| Create or modify files safely | `write_to_file` | Automated syntax validation (Python, JSON, YAML, XML), auto `mkdir -p` |

---

## 1. The `find_by_name` Tool

Find files or directories matching a glob pattern or filename with directory depth and exclusion filters.

### 📝 PARAMETERS:
- `search_directory`: **REQUIRED** - Absolute path of the root directory to search in.
- `pattern`: *OPTIONAL* - Filename glob pattern (e.g. `"*.py"`, `"*.json"`). Default: `"*"` (all files).
- `type`: *OPTIONAL* - Filter by item type: `"file"`, `"directory"`, or `"any"`. Default: `"any"`.
- `max_depth`: *OPTIONAL* - Maximum directory depth to recurse. Default: unlimited.
- `excludes`: *OPTIONAL* - Comma-separated path segments to exclude (e.g. `"node_modules,__pycache__,.git"`).
- `full_path`: *OPTIONAL* - Match pattern against the full path instead of filename only (`"true"` / `"false"`). Default: `"false"`.

### 📋 HOW TO CALL THIS TOOL:

Single-line CLI execution:
```bash
human-skills '{"tool_name": "find_by_name", "tool_args": {"search_directory": "/home/user_name/workdir/my-project", "pattern": "*.py", "type": "file", "max_depth": "3", "excludes": "node_modules,__pycache__,.git", "full_path": "false"}}'
```

Which maps to this JSON payload:
```json
{
    "tool_name": "find_by_name",
    "tool_args": {
        "search_directory":   "/home/user_name/workdir/my-project",
        "pattern":            "*.py",
        "type":               "file",
        "max_depth":          "3",
        "excludes":           "node_modules,__pycache__,.git",
        "full_path":          "false"
    }
}
```

Expected output:
```
Found 3 result(s) matching '*.py' in /home/user_name/workdir/my-project:
  main.py (1.4 KB)
  src/utils.py (3.2 KB)
  src/config.py (850 B)
```

### 📁 Common Scenarios for `find_by_name`:

#### Scenario A: Find all subdirectories
```bash
human-skills '{
    "tool_name": "find_by_name",
    "tool_args": {
        "search_directory":   "/home/user_name/workdir/my-project",
        "type":               "directory",
        "max_depth":          "2"
    }
}'
```

#### Scenario B: Find configuration files excluding caches
```bash
human-skills '{
    "tool_name": "find_by_name",
    "tool_args": {
        "search_directory":   "/home/user_name/workdir/my-project",
        "pattern":            "*.json",
        "excludes":           "node_modules,dist,build,.cache"
    }
}'
```

---

## 2. The `grep_search` Tool

High-speed code and text search across files with line numbers, code snippets, and AST context detection (classes, functions, async functions).

### 📝 PARAMETERS:
- `query`: **REQUIRED** - Text or symbol pattern to search for.
- `search_path`: *OPTIONAL* - Root directory or specific file path to search in. Default: `"."`.
- `case_insensitive`: *OPTIONAL* - Case-insensitive match (`"true"` / `"false"`). Default: `"false"`.
- `match_per_line`: *OPTIONAL* - Return each matching line with context (`"true"`), or filenames only (`"false"`). Default: `"true"`.
- `includes`: *OPTIONAL* - Comma-separated glob patterns to restrict search to specific file types (e.g. `"*.py,*.ts"`).

### 📋 HOW TO CALL THIS TOOL:

Single-line CLI execution:
```bash
human-skills '{"tool_name": "grep_search", "tool_args": {"query": "def execute", "search_path": "/home/user_name/workdir/my-project", "case_insensitive": "false", "match_per_line": "true", "includes": "*.py"}}'
```

Which maps to this JSON payload:
```json
{
    "tool_name": "grep_search",
    "tool_args": {
        "query":              "def execute",
        "search_path":        "/home/user_name/workdir/my-project",
        "case_insensitive":   "false",
        "match_per_line":     "true",
        "includes":           "*.py"
    }
}
```

Expected output:
```
Found 2 match(es) for 'def execute' in /home/user_name/workdir/my-project

📄 src/core.py
  L42 [async_function: execute]:     async def execute(self, **kwargs) -> Response:

📄 src/runner.py
  L18 [function: execute]:     def execute(command: str) -> None:
```

### 📁 Common Scenarios for `grep_search`:

#### Scenario A: Find all files mentioning a term (fast file listing)
```bash
human-skills '{
    "tool_name": "grep_search",
    "tool_args": {
        "query":              "Settings",
        "search_path":        "/home/user_name/workdir/my-project/src",
        "match_per_line":     "false",
        "includes":           "*.py"
    }
}'
```

#### Scenario B: Case-insensitive search across documentation and code
```bash
human-skills '{
    "tool_name": "grep_search",
    "tool_args": {
        "query":              "authentication",
        "search_path":        "/home/user_name/workdir/my-project",
        "case_insensitive":   "true",
        "match_per_line":     "true",
        "includes":           "*.py,*.md"
    }
}'
```

---

## 3. The `list_dir` Tool

Inspect directory contents and display a clean Markdown table with file types, human-readable sizes, modification timestamps, and POSIX permissions.

### 📝 PARAMETERS:
- `directory_path`: **REQUIRED** - Absolute path to the directory to list.

### 📋 HOW TO CALL THIS TOOL:

Single-line CLI execution:
```bash
human-skills '{"tool_name": "list_dir", "tool_args": {"directory_path": "/home/user_name/workdir/my-project"}}'
```

Which maps to this JSON payload:
```json
{
    "tool_name": "list_dir",
    "tool_args": {
        "directory_path":     "/home/user_name/workdir/my-project"
    }
}
```

Expected output:
```markdown
Contents of `/home/user_name/workdir/my-project`:

| Name | Type | Size | Modified | Permissions |
|------|------|------|----------|-------------|
| src/ | Dir | 12 files | 2026-09-20 14:30 | rwxr-xr-x |
| tests/ | Dir | 5 files | 2026-09-20 14:25 | rwxr-xr-x |
| main.py | File | 1.4 KB | 2026-09-20 14:28 | rw-r--r-- |
| pyproject.toml | File | 850 B | 2026-09-20 11:00 | rw-r--r-- |
| README.md | File | 2.1 KB | 2026-09-20 10:15 | rw-r--r-- |
```

### 📁 Common Scenarios for `list_dir`:

#### Scenario A: Inspect source package directory
```bash
human-skills '{
    "tool_name": "list_dir",
    "tool_args": {
        "directory_path":     "/home/user_name/workdir/my-project/src"
    }
}'
```

#### Scenario B: Check build output directory
```bash
human-skills '{
    "tool_name": "list_dir",
    "tool_args": {
        "directory_path":     "/home/user_name/workdir/my-project/dist"
    }
}'
```

---

## 4. The `view_file` Tool

Read and inspect file contents with 1-indexed line numbers, total line count metadata, and optional line range slicing.

### 📝 PARAMETERS:
- `absolute_path`: **REQUIRED** - Absolute path to the file to view.
- `start_line`: *OPTIONAL* - First line to display (1-indexed). Default: `1`.
- `end_line`: *OPTIONAL* - Last line to display (inclusive). Default: show up to end of file.

### 📋 HOW TO CALL THIS TOOL:

Single-line CLI execution:
```bash
human-skills '{"tool_name": "view_file", "tool_args": {"absolute_path": "/home/user_name/workdir/my-project/main.py", "start_line": "1", "end_line": "15"}}'
```

Which maps to this JSON payload:
```json
{
    "tool_name": "view_file",
    "tool_args": {
        "absolute_path":      "/home/user_name/workdir/my-project/main.py",
        "start_line":         "1",
        "end_line":           "15"
    }
}
```

Expected output:
```
File: /home/user_name/workdir/my-project/main.py  |  Total lines: 45  |  Showing: L1–L15
────────────────────────────────────────────────────────────────────────
1: import os
2: import sys
3: from pathlib import Path
4: 
5: def main():
6:     print("Application starting...")
7: 
8: if __name__ == "__main__":
9:     main()
```

### 📁 Common Scenarios for `view_file`:

#### Scenario A: View entire file from beginning
```bash
human-skills '{
    "tool_name": "view_file",
    "tool_args": {
        "absolute_path":      "/home/user_name/workdir/my-project/pyproject.toml"
    }
}'
```

#### Scenario B: View specific function or error slice
```bash
human-skills '{
    "tool_name": "view_file",
    "tool_args": {
        "absolute_path":      "/home/user_name/workdir/my-project/src/services.py",
        "start_line":         "40",
        "end_line":           "85"
    }
}'
```

---

## 5. The `write_to_file` Tool

Create new files or overwrite existing ones safely. Includes automatic parent directory creation (`mkdir -p`) and multi-language syntax checking.

### 📝 PARAMETERS:
- `target_file`: **REQUIRED** - Absolute path for the new file.
- `code_content`: *OPTIONAL* - Content to write to the file. Default: empty string.
- `overwrite`: *OPTIONAL* - Overwrite existing file if `"true"`. Default: `"false"`.
- `auto_check`: *OPTIONAL* - Validate syntax before writing (`"true"` / `"false"`). Default: `"true"`. Supports `.py` (`ast` + `py_compile`), `.json`, `.yaml`, `.xml`.
- `strict_mode`: *OPTIONAL* - Block file creation on syntax errors if `"true"`. Default: `"true"`.

### 📋 HOW TO CALL THIS TOOL:

Single-line CLI execution:
```bash
human-skills '{"tool_name": "write_to_file", "tool_args": {"target_file": "/home/user_name/workdir/my-project/src/config.py", "code_content": "PORT = 8080\nDEBUG = True\n", "overwrite": "true", "auto_check": "true", "strict_mode": "true"}}'
```

Which maps to this JSON payload:
```json
{
    "tool_name": "write_to_file",
    "tool_args": {
        "target_file":        "/home/user_name/workdir/my-project/src/config.py",
        "code_content":       "PORT = 8080\nDEBUG = True\n",
        "overwrite":          "true",
        "auto_check":         "true",
        "strict_mode":        "true"
    }
}
```

Expected output:
```
✅ File created: /home/user_name/workdir/my-project/src/config.py
   Size    : 25 B
   Lines   : 2
   Syntax  : ✓ passed
```

### 📁 Common Scenarios for `write_to_file`:

#### Scenario A: Create a new Python module
```bash
human-skills '{
    "tool_name": "write_to_file",
    "tool_args": {
        "target_file":        "/home/user_name/workdir/my-project/src/helpers.py",
        "code_content":       "def format_name(first: str, last: str) -> str:\n    return f\"{first.strip()} {last.strip()}\"\n",
        "overwrite":          "false",
        "auto_check":         "true",
        "strict_mode":        "true"
    }
}'
```

#### Scenario B: Create a JSON configuration file
```bash
human-skills '{
    "tool_name": "write_to_file",
    "tool_args": {
        "target_file":        "/home/user_name/workdir/my-project/config/settings.json",
        "code_content":       "{\n  \"env\": \"production\",\n  \"retries\": 3\n}\n",
        "overwrite":          "true",
        "auto_check":         "true"
    }
}'
```

#### Scenario C: Create an empty placeholder file
```bash
human-skills '{
    "tool_name": "write_to_file",
    "tool_args": {
        "target_file":        "/home/user_name/workdir/my-project/src/__init__.py",
        "code_content":       "",
        "overwrite":          "true"
    }
}'
```

---

## ⚠️ Important Rules & Best Practices

1. **All values in `tool_args` must be strings**:
   - Numbers and booleans must be quoted strings: `"max_depth": "3"`, `"match_per_line": "true"`, `"start_line": "1"`.
2. **Always supply absolute paths**:
   - Use absolute paths (e.g. `/home/user/project/...`) to ensure deterministic behavior across subshells.
3. **Safety First on File Writes**:
   - `write_to_file` will refuse to overwrite existing files unless `"overwrite": "true"` is explicitly passed.
   - If syntax validation fails in strict mode, the file is not written and specific errors with line numbers are returned.
4. **Token Efficiency**:
   - Use `view_file` with `start_line` and `end_line` for targeted reviews rather than dumping massive files.
   - Use `grep_search` with `includes` to avoid searching irrelevant directories and files.
