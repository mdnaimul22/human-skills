from __future__ import annotations
import asyncio
import threading
from typing import Callable
import schedule as schedule_lib
from src.config import Settings, setup_logger
from src.helpers import get_now_iso, get_now_utc
from src.apps.git.helpers import (
    CommitEngine, ConfigWatcher, ForwardEngine, ProjectRegistry,
    UpstreamEngine, load_memory, save_memory,
)
from src.apps.git.providers import get_status
from src.apps.git.schema import (
    ProjectCreate, ProjectDetail, ProjectMeta, ProjectUpdate, SyncResult,
)

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.manager")
SyncCallback = Callable[[SyncResult], None]


class WorkerState:
    __slots__ = (
        "project", "thread", "stop_event", "wakeup_event",
        "sync_trigger", "sync_lock", "scheduler", "watcher",
    )

    def __init__(
        self,
        project: ProjectMeta,
        thread: threading.Thread,
        stop_event: threading.Event,
        wakeup_event: threading.Event,
        sync_trigger: threading.Event,
        sync_lock: threading.Lock,
        scheduler: schedule_lib.Scheduler,
        watcher: ConfigWatcher,
    ) -> None:
        self.project = project
        self.thread = thread
        self.stop_event = stop_event
        self.wakeup_event = wakeup_event
        self.sync_trigger = sync_trigger
        self.sync_lock = sync_lock
        self.scheduler = scheduler
        self.watcher = watcher


class GitManager:
    _instance: GitManager | None = None
    _initialized: bool = False

    def __new__(cls, data_dir: str | None = None) -> GitManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str | None = None) -> None:
        if self._initialized:
            return
        self._data_dir = data_dir or Settings.RAW_GITSYNC_DATA_DIR
        self._registry = ProjectRegistry(data_dir=self._data_dir)
        self._lock = threading.Lock()
        self._workers: dict[str, WorkerState] = {}
        self._sync_locks: dict[str, threading.Lock] = {}
        self._last_results: dict[str, SyncResult] = {}
        self._sync_callbacks: dict[str, list[SyncCallback]] = {}
        self._initialized = True
        logger.info(f"GitManager initialized (data_dir={self._data_dir})")

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance is not None:
            cls._instance.stop_all()
        cls._instance = None
        cls._initialized = False

    def _project_sync_lock(self, project_id: str) -> threading.Lock:
        with self._lock:
            lock = self._sync_locks.get(project_id)
            if lock is None:
                lock = threading.Lock()
                self._sync_locks[project_id] = lock
            return lock

    def list_projects(self) -> list[ProjectMeta]:
        running = set(self.running_ids())
        projects = self._registry.load_registry()
        for proj in projects:
            if proj.id in running:
                proj.status = "running"
        return projects

    def get_project(self, project_id: str) -> ProjectDetail:
        detail = self._registry.get(project_id)
        if self.is_running(project_id):
            detail.status = "running"
        detail.last_result = self._last_results.get(project_id)
        return detail

    def create_project(self, data: ProjectCreate) -> ProjectMeta:
        return self._registry.create(data)

    def update_project(self, project_id: str, data: ProjectUpdate) -> ProjectDetail:
        detail = self._registry.update(project_id, data)
        if self.is_running(project_id):
            detail.status = "running"
        detail.last_result = self._last_results.get(project_id)
        return detail

    def register_sync_callback(self, project_id: str, callback: SyncCallback) -> None:
        with self._lock:
            callbacks = self._sync_callbacks.setdefault(project_id, [])
            if callback not in callbacks:
                callbacks.append(callback)

    def unregister_sync_callback(self, project_id: str, callback: SyncCallback) -> None:
        with self._lock:
            callbacks = self._sync_callbacks.get(project_id)
            if callbacks and callback in callbacks:
                callbacks.remove(callback)

    def _dispatch_sync_callbacks(self, project_id: str, result: SyncResult) -> None:
        with self._lock:
            callbacks = list(self._sync_callbacks.get(project_id, []))
        for callback in callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"[{project_id}] Post-sync callback failed: {e}")

    def delete_project(self, project_id: str) -> None:
        self.stop_project(project_id)
        self._registry.delete(project_id)
        with self._lock:
            self._last_results.pop(project_id, None)
            self._sync_locks.pop(project_id, None)
            self._sync_callbacks.pop(project_id, None)

    def sync_project(self, project_id: str) -> SyncResult:
        detail = self._registry.get(project_id)
        watcher = ConfigWatcher(detail.id, detail.path, data_dir=self._data_dir)
        lock = self._project_sync_lock(project_id)
        with lock:
            return self._execute_sync(watcher)

    async def sync_project_async(self, project_id: str) -> SyncResult:
        return await asyncio.to_thread(self.sync_project, project_id)

    def _execute_sync(self, watcher: ConfigWatcher) -> SyncResult:
        project_id = watcher.project_id
        repo_root = watcher.project_path
        git_cfg = watcher.automation.git
        now_label = get_now_utc().strftime("%Y-%m-%d %H:%M")

        upstream_engine = UpstreamEngine(repo_root=repo_root)
        forward_engine = ForwardEngine(repo_root=repo_root)
        commit_engine = CommitEngine(repo_root=repo_root)

        pulls, updated_upstreams = upstream_engine.pull(watcher.upstreams, watcher.forwards)

        memory_rel = self._registry.memory_path(project_id)
        previous_memory = load_memory(memory_rel)
        removed_orphans = forward_engine.cleanup_orphans(previous_memory, watcher.forwards, watcher.upstreams)
        orphan_push_ok = commit_engine.commit_orphans(
            removed_orphans, git_cfg.branch, now_label, git_cfg.auto_push, auto_commit=git_cfg.auto_commit
        )

        copied_targets, current_memory = forward_engine.forward(watcher.forwards, watcher.upstreams)

        status_res = get_status(repo_root)
        upstream_changes = (
            commit_engine.classify_managed(status_res.output, watcher.forwards, watcher.upstreams)
            if status_res.ok and status_res.output.strip()
            else {}
        )
        push_ok, committed_upstreams = commit_engine.commit_and_push(
            upstream_changes=upstream_changes,
            branch=git_cfg.branch,
            current_time=now_label,
            commit_messages=git_cfg.commit_messages,
            auto_push=git_cfg.auto_push,
            auto_commit=git_cfg.auto_commit,
        )
        overall_ok = orphan_push_ok and push_ok

        if overall_ok or copied_targets or removed_orphans:
            save_memory(current_memory, memory_rel)

        result = SyncResult(
            project_id=project_id,
            pull_results=pulls,
            updated_upstreams=updated_upstreams,
            copied_targets=copied_targets,
            removed_orphans=removed_orphans,
            committed_upstreams=committed_upstreams,
            push_ok=overall_ok,
        )
        self._last_results[project_id] = result
        self._registry.update_status(
            project_id,
            status="idle" if overall_ok else "error",
            last_sync=get_now_iso(),
        )
        logger.info(
            f"[{project_id}] Sync finished | upstreams={sum(pulls.values())}/{len(pulls)} "
            f"| copied={len(copied_targets)} | orphans={len(removed_orphans)} | ok={overall_ok}"
        )
        if copied_targets or removed_orphans:
            self._dispatch_sync_callbacks(project_id, result)
        return result

    def start_project(self, project_id: str) -> bool:
        detail = self._registry.get(project_id)
        meta = ProjectMeta(
            id=detail.id,
            name=detail.name,
            path=detail.path,
            status=detail.status,
            last_sync=detail.last_sync,
            created_at=detail.created_at,
            updated_at=detail.updated_at,
        )
        with self._lock:
            existing = self._workers.get(project_id)
            if existing is not None and existing.thread.is_alive():
                return False
            self._workers.pop(project_id, None)
            sync_lock = self._sync_locks.setdefault(project_id, threading.Lock())
            stop_event = threading.Event()
            wakeup_event = threading.Event()
            sync_trigger = threading.Event()
            watcher = ConfigWatcher(meta.id, meta.path, data_dir=self._data_dir)
            sched = schedule_lib.Scheduler()
            state = WorkerState(
                project=meta,
                thread=threading.Thread(
                    target=self._worker_loop,
                    args=(meta.id, watcher, sched, stop_event, wakeup_event, sync_trigger, sync_lock),
                    name=f"gitsync-{meta.id}",
                    daemon=True,
                ),
                stop_event=stop_event,
                wakeup_event=wakeup_event,
                sync_trigger=sync_trigger,
                sync_lock=sync_lock,
                scheduler=sched,
                watcher=watcher,
            )
            self._workers[project_id] = state
            state.thread.start()
        logger.info(f"Started git sync worker: {project_id}")
        return True

    def start_all(self) -> dict[str, bool]:
        if not Settings.GITSYNC_ENABLED:
            logger.info("GitSync is disabled via env/.gitsync")
            return {}
        results: dict[str, bool] = {}
        for proj in self._registry.load_registry():
            results[proj.id] = self.start_project(proj.id)
        return results

    def stop_project(self, project_id: str, timeout: float = 5.0) -> bool:
        with self._lock:
            state = self._workers.get(project_id)
            if state is None:
                return False
            state.stop_event.set()
            state.wakeup_event.set()
        state.thread.join(timeout=timeout)
        with self._lock:
            if not state.thread.is_alive():
                self._workers.pop(project_id, None)
        logger.info(f"Stopped git sync worker: {project_id}")
        return True

    def stop_all(self, timeout: float = 5.0) -> None:
        with self._lock:
            states = list(self._workers.values())
            for state in states:
                state.stop_event.set()
                state.wakeup_event.set()
        for state in states:
            state.thread.join(timeout=timeout)
        with self._lock:
            self._workers.clear()
        logger.info("All git sync workers stopped")

    def is_running(self, project_id: str) -> bool:
        with self._lock:
            state = self._workers.get(project_id)
            return state is not None and state.thread.is_alive()

    def running_ids(self) -> list[str]:
        with self._lock:
            return [pid for pid, st in self._workers.items() if st.thread.is_alive()]

    def trigger_sync(self, project_id: str) -> bool:
        with self._lock:
            state = self._workers.get(project_id)
            if state is not None and state.thread.is_alive():
                state.sync_trigger.set()
                state.wakeup_event.set()
                return True
        self._registry.get(project_id)
        thread = threading.Thread(
            target=self._run_one_off,
            args=(project_id,),
            name=f"gitsync-once-{project_id}",
            daemon=True,
        )
        thread.start()
        return True

    def _run_one_off(self, project_id: str) -> None:
        try:
            self.sync_project(project_id)
        except Exception as e:
            logger.error(f"[{project_id}] One-off sync failed: {e}")

    def _run_locked_sync(self, watcher: ConfigWatcher, sync_lock: threading.Lock) -> None:
        try:
            with sync_lock:
                self._execute_sync(watcher)
        except Exception as e:
            logger.error(f"[{watcher.project_id}] Scheduled sync failed: {e}")

    def _register_schedule(
        self,
        sched: schedule_lib.Scheduler,
        watcher: ConfigWatcher,
        sync_lock: threading.Lock,
    ) -> None:
        run_at, interval_minutes = watcher.sched_params()
        if run_at:
            sched.every().day.at(run_at).do(self._run_locked_sync, watcher, sync_lock)
        else:
            sched.every(interval_minutes).minutes.do(self._run_locked_sync, watcher, sync_lock)

    def _worker_loop(
        self,
        project_id: str,
        watcher: ConfigWatcher,
        sched: schedule_lib.Scheduler,
        stop_event: threading.Event,
        wakeup_event: threading.Event,
        sync_trigger: threading.Event,
        sync_lock: threading.Lock,
    ) -> None:
        self._register_schedule(sched, watcher, sync_lock)
        self._run_locked_sync(watcher, sync_lock)

        while not stop_event.is_set():
            wakeup_event.wait(timeout=watcher.poll_interval)
            wakeup_event.clear()
            if stop_event.is_set():
                break
            if sync_trigger.is_set():
                sync_trigger.clear()
                self._run_locked_sync(watcher, sync_lock)
            if watcher.has_changed():
                watcher.reload()
                sched.clear()
                self._register_schedule(sched, watcher, sync_lock)
                self._run_locked_sync(watcher, sync_lock)
            sched.run_pending()

        with self._lock:
            self._workers.pop(project_id, None)


def get_git_manager(data_dir: str | None = None) -> GitManager:
    return GitManager(data_dir=data_dir)
