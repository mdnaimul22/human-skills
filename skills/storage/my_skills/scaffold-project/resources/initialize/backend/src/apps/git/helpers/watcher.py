from __future__ import annotations
import json
from typing import TypeVar
from pydantic import BaseModel, ValidationError as PydanticValidationError
from src.config import Settings, exists, get_mtime, read_json, setup_logger
from src.helpers import ValidationError
from src.apps.git.schema import (
    AutomationConfig, ConfigReloadDiff, ForwardConfigFile, ForwardRule,
    UpstreamConfigFile, UpstreamEntry,
)

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.helpers.watcher")
M = TypeVar("M", bound=BaseModel)


class ConfigWatcher:
    def __init__(self, project_id: str, project_path: str, data_dir: str | None = None) -> None:
        self.project_id = project_id
        self.project_path = project_path
        self.data_dir = data_dir or Settings.RAW_GITSYNC_DATA_DIR
        self._mtimes: dict[str, float] = {}
        self.upstreams: list[UpstreamEntry] = []
        self.forwards: list[ForwardRule] = []
        self.automation: AutomationConfig = AutomationConfig()
        self._do_load()

    @property
    def _config_files(self) -> list[str]:
        return [
            Settings.GITSYNC_UPSTREAM_FILE,
            Settings.GITSYNC_FORWARD_FILE,
            Settings.GITSYNC_AUTOMATION_FILE,
        ]

    def _file_rel(self, filename: str) -> str:
        return f"{self.data_dir}/{self.project_id}/{filename}"

    def _snapshot_mtimes(self) -> None:
        for filename in self._config_files:
            rel = self._file_rel(filename)
            self._mtimes[rel] = get_mtime(rel) if exists(rel) else 0.0

    def _load_model(self, filename: str, model_cls: type[M]) -> M:
        rel = self._file_rel(filename)
        if not exists(rel):
            return model_cls()
        try:
            return model_cls.model_validate(read_json(rel))
        except (OSError, json.JSONDecodeError, PydanticValidationError) as e:
            logger.error(f"Invalid git config '{rel}': {e}")
            raise ValidationError(f"Invalid git config '{rel}': {e}") from e

    def _do_load(self) -> None:
        self.upstreams = self._load_model(Settings.GITSYNC_UPSTREAM_FILE, UpstreamConfigFile).upstreams
        self.forwards = self._load_model(Settings.GITSYNC_FORWARD_FILE, ForwardConfigFile).forwards
        self.automation = self._load_model(Settings.GITSYNC_AUTOMATION_FILE, AutomationConfig)
        self._snapshot_mtimes()

    def sched_params(self) -> tuple[str | None, int]:
        return self.automation.schedule.run_at, self.automation.schedule.interval_minutes

    @property
    def poll_interval(self) -> int:
        return self.automation.schedule.poll_interval_seconds

    def has_changed(self) -> bool:
        for filename in self._config_files:
            rel = self._file_rel(filename)
            mtime = get_mtime(rel) if exists(rel) else 0.0
            if self._mtimes.get(rel) != mtime:
                return True
        return False

    def reload(self) -> ConfigReloadDiff:
        old_sched = self.sched_params()
        old_up_count = len(self.upstreams)
        old_fwd_count = len(self.forwards)
        self._do_load()
        return ConfigReloadDiff(
            upstreams_before=old_up_count,
            upstreams_after=len(self.upstreams),
            forwards_before=old_fwd_count,
            forwards_after=len(self.forwards),
            schedule_changed=(old_sched != self.sched_params()),
        )
