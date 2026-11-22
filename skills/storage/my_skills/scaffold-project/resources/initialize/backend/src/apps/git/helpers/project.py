from __future__ import annotations
import json
import re
import threading
from typing import TypeVar
from pydantic import BaseModel, ValidationError as PydanticValidationError
from src.config import (
    Settings, delete, ensure_dir, exists, read_json, setup_logger, write_json,
)
from src.helpers import NotFoundError, ValidationError, get_now_iso
from src.apps.git.schema import (
    AutomationConfig, ForwardConfigFile, ForwardRule, GitConfig,
    PROJECT_META_LIST_ADAPTER, ProjectCreate, ProjectDetail, ProjectMeta,
    ProjectStatus, ProjectUpdate, ScheduleConfig, UpstreamConfigFile,
    UpstreamEntry, generate_hash_id,
)

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.helpers.project")
M = TypeVar("M", bound=BaseModel)


class ProjectRegistry:
    def __init__(self, data_dir: str | None = None) -> None:
        self._lock = threading.Lock()
        self.data_dir = data_dir or Settings.RAW_GITSYNC_DATA_DIR

    def registry_path(self) -> str:
        return f"{self.data_dir}/{Settings.GITSYNC_PROJECTS_FILE}"

    def project_dir(self, project_id: str) -> str:
        return f"{self.data_dir}/{project_id}"

    def memory_path(self, project_id: str) -> str:
        return f"{self.project_dir(project_id)}/{Settings.GITSYNC_MEMORY_FILE}"

    @staticmethod
    def slugify(text: str) -> str:
        cleaned = re.sub(r"[^\w\s-]", "", text.lower().strip())
        cleaned = re.sub(r"[\s_]+", "-", cleaned).strip("-")
        return cleaned or "untitled"

    def _file_rel(self, project_id: str, filename: str) -> str:
        return f"{self.project_dir(project_id)}/{filename}"

    def load_registry(self) -> list[ProjectMeta]:
        rel = self.registry_path()
        if not exists(rel):
            return []
        try:
            return PROJECT_META_LIST_ADAPTER.validate_python(read_json(rel))
        except (OSError, json.JSONDecodeError, PydanticValidationError) as e:
            logger.error(f"Corrupted git project registry '{rel}': {e}")
            raise ValidationError(f"Corrupted git project registry '{rel}': {e}") from e

    def save_registry(self, projects: list[ProjectMeta]) -> None:
        rel = self.registry_path()
        ensure_dir(self.data_dir)
        write_json(rel, [p.model_dump() for p in projects])

    def _read_model(self, project_id: str, filename: str, model_cls: type[M]) -> M:
        rel = self._file_rel(project_id, filename)
        if not exists(rel):
            return model_cls()
        try:
            return model_cls.model_validate(read_json(rel))
        except (OSError, json.JSONDecodeError, PydanticValidationError) as e:
            raise ValidationError(f"Invalid git config '{rel}': {e}") from e

    def _normalize_forwards(
        self,
        forwards: list[ForwardRule],
        upstreams: list[UpstreamEntry],
    ) -> list[ForwardRule]:
        up_by_name = {u.project_name: u.upstream_id for u in upstreams if u.project_name}
        up_by_path = {u.path.rstrip("/"): u.upstream_id for u in upstreams if u.path}
        up_by_id = {u.upstream_id: u.project_name for u in upstreams if u.upstream_id}
        normalized: list[ForwardRule] = []
        for rule in forwards:
            item = rule.model_copy()
            if not item.upstream_id:
                item.upstream_id = self._infer_upstream_id(item, up_by_name, up_by_path)
            if item.upstream_id in up_by_id:
                item.project_name = up_by_id[item.upstream_id]
            elif item.upstream_id:
                item.upstream_id = ""
                item.project_name = ""
            normalized.append(item)
        return normalized

    @staticmethod
    def _infer_upstream_id(
        rule: ForwardRule,
        up_by_name: dict[str, str],
        up_by_path: dict[str, str],
    ) -> str:
        if rule.project_name and rule.project_name in up_by_name:
            return up_by_name[rule.project_name]
        if rule.from_path:
            src_clean = rule.from_path.rstrip("/")
            for up_path, up_id in up_by_path.items():
                if src_clean == up_path or src_clean.startswith(f"{up_path}/"):
                    return up_id
        return ""

    def load_project_configs(
        self,
        project_id: str,
    ) -> tuple[list[UpstreamEntry], list[ForwardRule], AutomationConfig]:
        upstreams = self._read_model(project_id, Settings.GITSYNC_UPSTREAM_FILE, UpstreamConfigFile).upstreams
        raw_forwards = self._read_model(project_id, Settings.GITSYNC_FORWARD_FILE, ForwardConfigFile).forwards
        forwards = self._normalize_forwards(raw_forwards, upstreams)
        automation = self._read_model(project_id, Settings.GITSYNC_AUTOMATION_FILE, AutomationConfig)
        return upstreams, forwards, automation

    def create(self, data: ProjectCreate) -> ProjectMeta:
        with self._lock:
            base_id = self.slugify(data.name)
            existing = self.load_registry()
            existing_ids = {p.id for p in existing}
            project_id = base_id
            counter = 1
            while project_id in existing_ids:
                project_id = f"{base_id}-{counter}"
                counter += 1
            now = get_now_iso()
            meta = ProjectMeta(
                id=project_id,
                name=data.name,
                path=data.path,
                created_at=now,
                updated_at=now,
            )
            existing.append(meta)
            self.save_registry(existing)

        ensure_dir(self.project_dir(project_id))
        write_json(self._file_rel(project_id, Settings.GITSYNC_UPSTREAM_FILE), UpstreamConfigFile().model_dump())
        write_json(self._file_rel(project_id, Settings.GITSYNC_FORWARD_FILE), ForwardConfigFile().model_dump())
        write_json(
            self._file_rel(project_id, Settings.GITSYNC_AUTOMATION_FILE),
            AutomationConfig(schedule=ScheduleConfig(), git=GitConfig()).model_dump(),
        )
        write_json(self.memory_path(project_id), [])
        logger.info(f"Created git project: {meta.name} ({project_id})")
        return meta

    def _write_updated_upstreams(
        self,
        project_id: str,
        upstreams: list[UpstreamEntry],
        sync_existing_forwards: bool,
    ) -> dict[str, str]:
        up_map: dict[str, str] = {}
        prepared: list[UpstreamEntry] = []
        for entry in upstreams:
            item = entry.model_copy()
            if not item.upstream_id:
                item.upstream_id = generate_hash_id()
            up_map[item.upstream_id] = item.project_name
            prepared.append(item)
        write_json(
            self._file_rel(project_id, Settings.GITSYNC_UPSTREAM_FILE),
            {"upstreams": [u.model_dump() for u in prepared]},
        )
        if sync_existing_forwards:
            self._sync_forwards_with_upstreams(project_id, up_map)
        return up_map

    def _sync_forwards_with_upstreams(self, project_id: str, up_map: dict[str, str]) -> None:
        existing_forwards = self._read_model(project_id, Settings.GITSYNC_FORWARD_FILE, ForwardConfigFile).forwards
        if not existing_forwards:
            return
        updated_any = False
        synced: list[ForwardRule] = []
        for rule in existing_forwards:
            item = rule.model_copy()
            if item.upstream_id:
                if item.upstream_id in up_map and item.project_name != up_map[item.upstream_id]:
                    item.project_name = up_map[item.upstream_id]
                    updated_any = True
                elif item.upstream_id not in up_map:
                    item.upstream_id = ""
                    item.project_name = ""
                    updated_any = True
            synced.append(item)
        if updated_any:
            write_json(
                self._file_rel(project_id, Settings.GITSYNC_FORWARD_FILE),
                {"forwards": [f.model_dump(by_alias=True) for f in synced]},
            )

    def _write_updated_forwards(
        self,
        project_id: str,
        forwards: list[ForwardRule],
        up_map: dict[str, str],
    ) -> None:
        seen_ids: set[str] = set()
        seen_keys: set[tuple[str, str, str]] = set()
        cleaned: list[ForwardRule] = []
        for rule in forwards:
            item = rule.model_copy()
            if not item.forward_id:
                item.forward_id = generate_hash_id()
            if item.forward_id in seen_ids:
                continue
            seen_ids.add(item.forward_id)
            if item.upstream_id in up_map:
                item.project_name = up_map[item.upstream_id]
            elif item.upstream_id:
                item.upstream_id = ""
                item.project_name = ""
            if item.from_path and item.to_path:
                key = (item.upstream_id, item.from_path, item.to_path)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
            cleaned.append(item)
        write_json(
            self._file_rel(project_id, Settings.GITSYNC_FORWARD_FILE),
            {"forwards": [f.model_dump(by_alias=True) for f in cleaned]},
        )

    def update(self, project_id: str, data: ProjectUpdate) -> ProjectDetail:
        with self._lock:
            projects = self.load_registry()
            meta = next((p for p in projects if p.id == project_id), None)
            if meta is None:
                raise NotFoundError("GitProject", project_id)

            up_map: dict[str, str]
            if data.upstreams is not None:
                up_map = self._write_updated_upstreams(project_id, data.upstreams, data.forwards is None)
            else:
                existing_ups = self._read_model(project_id, Settings.GITSYNC_UPSTREAM_FILE, UpstreamConfigFile).upstreams
                up_map = {u.upstream_id: u.project_name for u in existing_ups if u.upstream_id}

            if data.forwards is not None:
                self._write_updated_forwards(project_id, data.forwards, up_map)

            if data.git is not None or data.schedule is not None:
                automation = self._read_model(project_id, Settings.GITSYNC_AUTOMATION_FILE, AutomationConfig)
                if data.schedule is not None:
                    automation.schedule = data.schedule
                if data.git is not None:
                    automation.git = data.git
                write_json(self._file_rel(project_id, Settings.GITSYNC_AUTOMATION_FILE), automation.model_dump())

            meta.updated_at = get_now_iso()
            self.save_registry(projects)
            logger.info(f"Updated git project: {project_id}")
        return self.get(project_id)

    def get(self, project_id: str) -> ProjectDetail:
        projects = self.load_registry()
        meta = next((p for p in projects if p.id == project_id), None)
        if meta is None:
            raise NotFoundError("GitProject", project_id)
        upstreams, forwards, automation = self.load_project_configs(project_id)
        return ProjectDetail(
            **meta.model_dump(),
            upstreams=upstreams,
            forwards=forwards,
            git=automation.git,
            schedule=automation.schedule,
        )

    def delete(self, project_id: str) -> None:
        with self._lock:
            projects = self.load_registry()
            filtered = [p for p in projects if p.id != project_id]
            if len(filtered) == len(projects):
                raise NotFoundError("GitProject", project_id)
            self.save_registry(filtered)
        proj_dir = self.project_dir(project_id)
        if exists(proj_dir):
            delete(proj_dir)
        logger.info(f"Deleted git project: {project_id}")

    def update_status(self, project_id: str, status: ProjectStatus, last_sync: str | None = None) -> None:
        with self._lock:
            projects = self.load_registry()
            for proj in projects:
                if proj.id == project_id:
                    proj.status = status
                    if last_sync is not None:
                        proj.last_sync = last_sync
                    break
            self.save_registry(projects)
