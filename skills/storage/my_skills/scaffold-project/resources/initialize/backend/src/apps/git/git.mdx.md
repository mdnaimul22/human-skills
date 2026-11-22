# git.py DOX

> *`src/apps/git/` acts as the "Autonomous Upstream Git Synchronization & Managed-Path Control Plane":*
> *It decouples project registry, config watching, blobless/sparse upstream fetching, atomic forwarding, orphan cleanup, and surgical git commit/push into isolated sub-engines.*
> *It reads global defaults from `env/.gitsync` and declarative per-project specifications from `data/gitsync/` so external upstream repositories stay synchronized cleanly without disturbing host backend development.*

## Purpose

- Own the `src/apps/git` internal, FastAPI-free, auth-free Git synchronization engine and background worker orchestrator.
- Manage multi-project declarative configs (`projects.json`, `upstream.json`, `forward.json`, `automation.json`, `memory.json`) under `data/gitsync/` validated with Pydantic v2 models & TypeAdapters.
- Fetch external upstream repositories efficiently using blobless (`--filter=blob:none`) and cone sparse-checkout clones with automatic standard-clone fallback.
- Forward upstream files and directories into managed target paths using incremental POSIX atomic replace (`os.replace`) while ignoring `.git`, `__pycache__`, and `*.pyc`.
- Track forwarding lineage in `memory.json` to automatically detect and prune orphaned targets on rule or upstream changes.
- Execute strictly scoped surgical commits (`git commit --only -- <managed_paths>`) and fail-fast branch-validated pushes without disturbing unrelated working-tree or staged files.
- Dispatch registered post-sync callbacks for live hot-reload integration.
- Keep this module-level DOX profile synchronized with `src/apps/git/` implementation files.

## Ownership

- `src/apps/git/manager.py` owns the public facade and lifecycle orchestrator (`GitManager`, `WorkerState`).
- `src/apps/git/helpers/` owns the isolated sub-engine worker implementations (`project.py`, `watcher.py`, `upstream.py`, `orphan.py`, `forwarder.py`, `classifier.py`, `commit.py`).
- `src/apps/git/providers/git.py` owns low-level `git` CLI subprocess execution and stale lock recovery.
- `src/apps/git/schema/models.py` owns all Pydantic v2 schemas and TypeAdapters.
- `src/apps/git/__init__.py` owns PEP 562 lazy public exports (`_LAZY_EXPORTS`, `__getattr__`).
- `git.mdx.md` owns durable notes about responsibilities, runtime contracts, side effects, key concepts, work guidance, and verification.
- **Classes:**
  - `GitManager` (Public Facade / Orchestrator in `manager.py`)
    - `list_projects(self) -> list[ProjectMeta]`
    - `get_project(self, project_id: str) -> ProjectDetail`
    - `create_project(self, data: ProjectCreate) -> ProjectMeta`
    - `update_project(self, project_id: str, data: ProjectUpdate) -> ProjectDetail`
    - `delete_project(self, project_id: str) -> None`
    - `register_sync_callback(self, project_id: str, callback: SyncCallback) -> None`
    - `unregister_sync_callback(self, project_id: str, callback: SyncCallback) -> None`
    - `sync_project(self, project_id: str) -> SyncResult`
    - `sync_project_async(self, project_id: str) -> SyncResult`
    - `start_project(self, project_id: str) -> bool`
    - `start_all(self) -> dict[str, bool]`
    - `stop_project(self, project_id: str, timeout: float = 5.0) -> bool`
    - `stop_all(self, timeout: float = 5.0) -> None`
    - `is_running(self, project_id: str) -> bool`
    - `running_ids(self) -> list[str]`
    - `trigger_sync(self, project_id: str) -> bool`
    - `reset_instance(cls) -> None`
  - `WorkerState` (`manager.py`)
    - Slotted per-project worker state container holding `project`, `thread`, `stop_event`, `wakeup_event`, `sync_trigger`, `sync_lock`, `scheduler`, and `watcher`.
  - `ProjectRegistry` (`helpers/project.py`)
    - Multi-project registry, slug generation, rule normalization, and per-project JSON config persistence.
    - `registry_path(self) -> str`
    - `project_dir(self, project_id: str) -> str`
    - `memory_path(self, project_id: str) -> str`
    - `slugify(text: str) -> str`
    - `load_registry(self) -> list[ProjectMeta]`
    - `save_registry(self, projects: list[ProjectMeta]) -> None`
    - `load_project_configs(self, project_id: str) -> tuple[list[UpstreamEntry], list[ForwardRule], AutomationConfig]`
    - `create(self, data: ProjectCreate) -> ProjectMeta`
    - `update(self, project_id: str, data: ProjectUpdate) -> ProjectDetail`
    - `get(self, project_id: str) -> ProjectDetail`
    - `delete(self, project_id: str) -> None`
    - `update_status(self, project_id: str, status: ProjectStatus, last_sync: str | None = None) -> None`
  - `ConfigWatcher` (`helpers/watcher.py`)
    - Mtime-based declarative config monitor and hot-reload differ for per-project JSON files.
    - `sched_params(self) -> tuple[str | None, int]`
    - `poll_interval` (property `-> int`)
    - `has_changed(self) -> bool`
    - `reload(self) -> ConfigReloadDiff`
  - `UpstreamResolver` (`helpers/upstream.py`)
    - `resolve_sparse_subpaths(entry: UpstreamEntry, forwards: list[ForwardRule], repo_root: str = "") -> list[str]`
  - `UpstreamEngine` (`helpers/upstream.py`)
    - Sparse/blobless upstream cloner and `fetch` + hard-reset synchronizer.
    - `pull(self, upstreams: list[UpstreamEntry], forwards: list[ForwardRule]) -> tuple[dict[str, bool], list[str]]`
  - `OrphanEngine` (`helpers/orphan.py`)
    - Lineage comparator detecting deleted upstreams, removed/disabled rules, and renamed destinations.
    - `detect_orphans(self, previous: list[MemoryEntry], current: list[ForwardRule], upstreams: list[UpstreamEntry]) -> set[str]`
  - `ForwardEngine` (`helpers/forwarder.py`)
    - Boundary-guarded incremental file/directory copier, extraneous target pruner, and orphan remover.
    - `should_copy(src_path: str, dst_path: str) -> bool`
    - `ignore_copy_patterns(path: str, names: list[str]) -> set[str]`
    - `atomic_copy(src: str, dst: str) -> str`
    - `incremental_copy(src: str, dst: str) -> str`
    - `prune_extraneous(self, src_dir: str, dst_dir: str) -> list[str]`
    - `create_memory_entry(self, rule: ForwardRule) -> MemoryEntry`
    - `resolve_missing_source(self, src: str, rule: ForwardRule, upstreams: list[UpstreamEntry]) -> bool`
    - `forward(self, forwards: list[ForwardRule], upstreams: list[UpstreamEntry]) -> tuple[list[str], list[MemoryEntry]]`
    - `cleanup_orphans(self, previous: list[MemoryEntry], current: list[ForwardRule], upstreams: list[UpstreamEntry]) -> list[str]`
  - `ChangeClassifier` (`helpers/classifier.py`)
    - Maps `git status --porcelain -uall` changes strictly against enabled `ForwardRule.to_path` targets.
    - `classify_managed(self, status_output: str) -> dict[str, list[str]]`
    - `filter_staged_deletions(files: list[str], status_output: str) -> list[str]`
  - `CommitEngine` (`helpers/commit.py`)
    - Resolves active/configured push branch, commits managed batches with `--only`, and pushes cleanly.
    - `classify_managed(self, status_output: str, forwards: list[ForwardRule], upstreams: list[UpstreamEntry]) -> dict[str, list[str]]`
    - `commit_orphans(self, removed_paths: list[str], branch: str, current_time: str, auto_push: bool, auto_commit: bool = True) -> bool`
    - `commit_and_push(self, upstream_changes: dict[str, list[str]], branch: str, current_time: str, commit_messages: CommitMessages, auto_push: bool, auto_commit: bool = True) -> tuple[bool, list[str]]`
- **Provider Functions (`src/apps/git/providers/git.py`):**
  - `run_git(args: list[str], cwd: str, timeout: int | None = None) -> GitCommandResult`
  - `repo_is_dirty(repo_path: str) -> bool`
  - `get_status(repo_path: str) -> GitCommandResult`
- **Data Contracts (`src/apps/git/schema/models.py`):**
  - `GitCommandResult`, `UpstreamEntry`, `ForwardRule`, `MemoryEntry`, `CommitMessages`, `GitConfig`, `ScheduleConfig`, `AutomationConfig`
  - `UpstreamConfigFile`, `ForwardConfigFile`, `ConfigReloadDiff`, `SyncResult`, `ProjectStatus` (`"idle" | "running" | "error" | "paused"`)
  - `ProjectMeta`, `ProjectDetail`, `ProjectCreate`, `ProjectUpdate`
  - `PROJECT_META_LIST_ADAPTER` (Pydantic v2 TypeAdapter for `list[ProjectMeta]`)
  - `MEMORY_LIST_ADAPTER` (Pydantic v2 TypeAdapter for `list[MemoryEntry]`)
- **Top-level Functions:**
  - `get_git_manager(data_dir: str | None = None) -> GitManager` (`manager.py`)
  - `load_memory(rel: str) -> list[MemoryEntry]` (`helpers/forwarder.py`)
  - `save_memory(entries: list[MemoryEntry], rel: str) -> None` (`helpers/forwarder.py`)
  - `generate_hash_id() -> str` (`schema/models.py`)
- **Notable Constants/Configurations:**
  - `env/.gitsync` (`GITSYNC_ENABLED`, `GIT_AUTO_COMMIT`, `GIT_AUTO_PUSH`, `GIT_BRANCH`, `SYNC_INTERVAL_MINUTES`, `SYNC_POLL_SECONDS`, `GIT_TIMEOUT_SECONDS`)
  - `Settings.RAW_GITSYNC_DATA_DIR = "data/gitsync"`
  - `Settings.GITSYNC_PROJECTS_FILE = "projects.json"`
  - `Settings.GITSYNC_UPSTREAM_FILE = "upstream.json"`
  - `Settings.GITSYNC_FORWARD_FILE = "forward.json"`
  - `Settings.GITSYNC_AUTOMATION_FILE = "automation.json"`
  - `Settings.GITSYNC_MEMORY_FILE = "memory.json"`
  - `Settings.FFMPEG_GIT_PROJECT_ID = "vidula-ffmpeg"`
  - `_STALE_LOCK_SECONDS = 5.0` (`providers/git.py`)

## Runtime Contracts

- **Singleton & Lazy Import Pattern:**
  - External callers instantiate or retrieve `GitManager` via `GitManager()` or `get_git_manager()`.
  - `src/apps/git/__init__.py` uses PEP 562 `__getattr__` lazy resolution via `_LAZY_EXPORTS` so lightweight imports avoid pulling heavy dependencies eagerly.
- **Declarative Multi-Project Control Plane:**
  - Global defaults are loaded from `env/.gitsync` into `Settings`, while per-project behavior lives under `data/gitsync/<project_id>/` (`upstream.json`, `forward.json`, `automation.json`, `memory.json`).
  - Corrupted JSON config or memory files fail fast by raising `ValidationError`.
- **Blobless & Sparse Upstream Synchronization:**
  - `UpstreamEngine` derives cone sparse subpaths from enabled `ForwardRule.from_path` entries and clones with `--filter=blob:none` + `--no-checkout` + `sparse-checkout init --cone`, falling back to standard clone only if optimized clone fails.
- **Atomic Forwarding & Boundary Guards:**
  - Every forwarded file is written via `shutil.copy2` to a PID/UUID temporary file inside the target directory and promoted atomically with `os.replace`.
  - `_guard_managed_target` enforces `is_subpath(self.repo_root, target_abs)` and rejects empty, root, or `.git` paths.
  - Both copying (`ignore_copy_patterns`) and directory pruning (`_prune_level_files`, `_prune_level_dirs`) ignore `.git`, `__pycache__`, and `*.pyc` to prevent spurious sync cycles from Python bytecode generation.
- **Surgical Commits & Fail-Fast Push Branch Resolution:**
  - `ChangeClassifier` filters `git status --porcelain -uall` output so only paths under enabled `ForwardRule.to_path` targets are staged and committed via `git commit --only -- <managed_paths>`, leaving unrelated backend changes untouched.
  - When `auto_push=True`, `CommitEngine._resolve_push_branch()` verifies the active checked-out branch (`git rev-parse --abbrev-ref HEAD`); `"branch": "HEAD"` (or `"auto"` / `"current"` / `""`) resolves to the active branch, whereas any mismatch against an explicit branch name fails fast before committing.
- **Background Supervision & Post-Sync Callbacks:**
  - Each started project runs a daemon thread with `schedule`, `ConfigWatcher` mtime hot-reload (re-scheduling and triggering an immediate sync on config changes), and a per-project `sync_lock`.
  - `sync_project_async` bridges synchronous git work to threads via `asyncio.to_thread`.
  - Registered callbacks (`register_sync_callback`) fire whenever `copied_targets` or `removed_orphans` is non-empty.
- **Observed Side-Effect Areas:**
  - Execution of `git` CLI subprocesses (clone, fetch, reset, sparse-checkout, rm, add, commit, push, status, rev-parse) and automatic cleanup of stale `.git/*.lock` files older than `5.0s`.
  - File/directory writes, atomic replacements, and orphan deletions within managed target directories.
  - JSON state persistence under `data/gitsync/` (`projects.json`, `memory.json`).
  - Structured rotating logging to `logs/git.log`.
- **Imported Dependency Areas:**
  - `src.config` (`Settings`, `delete`, `ensure_dir`, `exists`, `get_abs_path`, `get_mtime`, `get_rel_path`, `get_size`, `is_dir`, `is_file`, `is_subpath`, `read_json`, `setup_logger`, `write_json`).
  - `src.helpers` (`NotFoundError`, `ValidationError`, `get_now_iso`, `get_now_utc`).
  - `pydantic` (`AliasChoices`, `BaseModel`, `ConfigDict`, `Field`, `TypeAdapter`, `ValidationError`).
  - `schedule` (thread-local job scheduler).

## Key Concepts

- **Sub-Engine Isolation ("Internal Machinery"):**
  - All registry, config-watching, upstream-fetching, orphan-detection, forwarding, classification, and commit workers live in `src/apps/git/helpers/` with low-level CLI execution isolated in `src/apps/git/providers/git.py`.
  - External callers interact exclusively with `src.apps.git` (`GitManager`, `get_git_manager`, schema contracts).
- **Lineage-Tracked Orphan Cleanup:**
  - Comparing previous `memory.json` entries against active `upstream.json` and `forward.json` definitions ensures removed or relocated upstream targets (for example moving FFmpeg assets out of `src/`) are cleanly untracked via `git rm --cached`, deleted from disk, and committed without leaving stale artifacts.
- **Zero-Interference Surgical Git Isolation:**
  - Separating managed upstream targets outside `src/` (e.g., `scripts/ffmpeg/scripts` and `scripts/ffmpeg/templates`) and using `--only` pathspecs ensures automated upstream sync commits never sweep in unrelated backend source modifications.
- **Autonomous Startup & Hot-Reload Coordination:**
  - During application lifespan startup (`main.py` `_bootstrap_ffmpeg_and_git`), `FFmpegManager.on_upstream_synced` is registered before `GitManager().start_all()` so cold boots and upstream sync events automatically refresh the downstream FFmpeg tool catalog.

## Work Guidance

- Never expose or import `src/apps/git/helpers/*` or `src/apps/git/providers/*` outside of `src/apps/git/`; always import public interfaces from `src.apps.git`.
- Forward external third-party upstream repositories outside `src/` (such as `scripts/ffmpeg/{scripts,templates}`) so full AST architecture linting on `src/` remains violation-free.
- Set `"branch": "HEAD"` in per-project `automation.json` to follow and push whichever active branch is checked out, or set an explicit branch name to enforce strict fail-fast branch matching.
- Keep `auto_commit`, `auto_push`, and `branch` settings explicit per project under `data/gitsync/<project_id>/automation.json` while retaining `env/.gitsync` as the global fallback baseline.
- Maintain zero-comment, zero-docstring, zero-`pathlib.Path`, and strict Pydantic/type-hint rules across all Python files in `src/apps/git/`.
- Always use the centralized logger configured for `logs/git.log`.

## Verification

- Run AST architecture compliance linter:
  ```bash
  human-skills '{"tool_name": "linter", "tool_args": {"scan_path": "src/apps/git"}}'
  ```
- Run targeted sub-engine and end-to-end manager test suites:
  ```bash
  PYTHONPATH=. pytest tests/apps/git/ -v --durations=0
  ```
- Related test suites:
  - `tests/apps/git/test_git_helpers.py`
  - `tests/apps/git/test_git_manager_e2e.py`

## Child DOX Index

- [manager.py](manager.py)
- [schema/models.py](schema/models.py)
- [providers/git.py](providers/git.py)
- [helpers/project.py](helpers/project.py)
- [helpers/watcher.py](helpers/watcher.py)
- [helpers/upstream.py](helpers/upstream.py)
- [helpers/orphan.py](helpers/orphan.py)
- [helpers/forwarder.py](helpers/forwarder.py)
- [helpers/classifier.py](helpers/classifier.py)
- [helpers/commit.py](helpers/commit.py)
