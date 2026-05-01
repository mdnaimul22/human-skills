---
trigger: always_on
name: config-path-rules
description: Strict rule — `from pathlib import Path` is FORBIDDEN outside config/. Every path operation must go through src.config utilities.
---

# Config Path Rules

> **`from pathlib import Path` is FORBIDDEN everywhere except inside `config/` itself.**

`config/files.py` already wraps every filesystem operation. The rest of the project — `services/`, `routers/`, `core/`, `providers/`, `helpers/`, `plugins/` — must **never** import `pathlib` directly.

## Why This Rule Exists

`files.py` provides a **relative-path API** rooted at `PROJECT_ROOT`. Every function accepts a `str` like `"data/cv/themes"` and internally resolves it to an absolute path. Bypassing this with raw `pathlib` creates:

- **Hidden hardcoding** — paths that break when `PROJECT_ROOT` changes
- **Duplicate resolution logic** — two sources of truth for where the project root is
- **Style inconsistency** — making the codebase impossible to audit

---

## Violation → Correct Pattern (Full Reference)

### ❌ Check if path exists
```python
# FORBIDDEN
from pathlib import Path
Path("data/cv/themes").exists()
Path(get_abs_path("data/cv/themes")).exists()
```
```python
# ✅ CORRECT
from src.config import exists
exists("data/cv/themes")
```

---

### ❌ Read a file
```python
# FORBIDDEN
Path("data/cv/themes/dark.json").read_text()
```
```python
# ✅ CORRECT
from src.config import read_text, read_json
content = read_text("data/cv/themes/dark.json")
data    = read_json("data/cv/themes/dark.json")
```

---

### ❌ Write a file
```python
# FORBIDDEN
Path("data/output/result.json").write_text(json.dumps(data))
```
```python
# ✅ CORRECT
from src.config import write_text, write_json
write_json("data/output/result.json", data)    # creates parent dirs automatically
write_text("data/output/result.txt", content)
```

---

### ❌ Create directories
```python
# FORBIDDEN
Path("data/user_data/wallet123").mkdir(parents=True, exist_ok=True)
Path(get_abs_path("data/user_data")).mkdir(parents=True, exist_ok=True)
```
```python
# ✅ CORRECT
from src.config import ensure_dir
ensure_dir("data/user_data/wallet123")
```

---

### ❌ Delete a file or directory
```python
# FORBIDDEN
Path("data/tmp/old.json").unlink()
shutil.rmtree(Path("data/tmp/old_dir"))
target = Path(get_abs_path("data/user")) / "sample.json"
target.unlink()
```
```python
# ✅ CORRECT
from src.config import delete
delete("data/tmp/old.json")        # file
delete("data/tmp/old_dir")         # directory (rmtree internally)
delete(f"{user_dir}/sample.json")  # composed relative path
```

---

### ❌ List files in a directory
```python
# FORBIDDEN
list(Path("data/cv/themes").glob("*.json"))
list(Path(get_abs_path("data/cv/components")).rglob("*.json"))
for d in Path(get_abs_path("data/user_data")).iterdir(): ...
```
```python
# ✅ CORRECT
from src.config import list_files
list_files("data/cv/themes", "*.json")          # shallow glob
list_files("data/cv/components", "**/*.json")   # recursive glob — same function
list_files("data/user_data", "*")               # all entries (files + dirs)

# Filtering by type — Path objects returned by list_files() are usable:
dirs = [e for e in list_files("data/user_data", "*") if e.is_dir()]
```
> `list_files()` returns `list[Path]` — you may call `.name`, `.is_dir()`,
> `.suffix`, `.relative_to()`, etc. on the **returned objects**.
> You just must not **import** `Path` yourself.

---

### ❌ Get absolute path (string)
```python
# FORBIDDEN
str(PROJECT_ROOT / "data" / "cv" / "themes")
```
```python
# ✅ CORRECT — only when an absolute str is unavoidable (e.g. passing to third-party lib)
from src.config import get_abs_path
abs_str = get_abs_path("data/cv/themes")   # → "/home/user/project/data/cv/themes"
```
> `get_abs_path` is the **escape hatch**. Use it only to interface with
> external libraries that require an absolute path string. Never use it
> to reconstruct a `Path` object: `Path(get_abs_path(...))` is **also forbidden**.

---

### ❌ Derive a parent directory
```python
# FORBIDDEN
parent = str(Path(rel).parent)
parent = Path(rel).parent.as_posix()
```
```python
# ✅ CORRECT — plain string split, no pathlib needed
parent = rel.rsplit("/", 1)[0]
# "data/user/wallet/format/sample.json" → "data/user/wallet/format"
```

---

## Complete `config` API Reference

| Need | Function | Import |
|:---|:---|:---|
| Check existence | `exists(rel)` | `from src.config import exists` |
| Read file as str | `read_text(rel)` | `from src.config import read_text` |
| Read file as dict | `read_json(rel)` | `from src.config import read_json` |
| Write str to file | `write_text(rel, content)` | `from src.config import write_text` |
| Write dict to file | `write_json(rel, data)` | `from src.config import write_json` |
| Create directories | `ensure_dir(rel)` | `from src.config import ensure_dir` |
| Delete file or dir | `delete(rel)` | `from src.config import delete` |
| List / glob files | `list_files(rel, pattern)` | `from src.config import list_files` |
| Absolute path str | `get_abs_path(rel)` | `from src.config import get_abs_path` |
| Project root | `PROJECT_ROOT` | `from src.config import PROJECT_ROOT` |

---

## Enforcement Checklist

Before every commit, verify in any file you touch:

- [ ] `from pathlib import Path` **does NOT appear** outside `config/`
- [ ] `import pathlib` **does NOT appear** outside `config/`
- [ ] `Path(...)` is **not constructed** anywhere outside `config/`
- [ ] `get_abs_path(...)` is **not wrapped** in `Path(get_abs_path(...))`
- [ ] Parent dirs are derived with `rel.rsplit("/", 1)[0]`, not `Path(rel).parent`
- [ ] File deletion uses `delete(rel)`, not `.unlink()` or `shutil.rmtree`
- [ ] Directory listing uses `list_files(rel, pattern)`, not `.iterdir()` or `.glob()` directly
