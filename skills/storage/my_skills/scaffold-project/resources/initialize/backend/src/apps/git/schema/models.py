from __future__ import annotations
import hashlib
import uuid
from typing import Literal
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, TypeAdapter
from src.config import Settings


def generate_hash_id() -> str:
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:8]


class GitCommandResult(BaseModel):
    ok: bool
    output: str


class UpstreamEntry(BaseModel):
    project_name: str = Field(default="unnamed", validation_alias=AliasChoices("project_name", "name"))
    upstream_id: str = Field(default_factory=generate_hash_id, validation_alias=AliasChoices("upstream_id", "id"))
    pull: bool = True
    sparse: bool = True
    blobless: bool = True
    branch: str = "main"
    path: str = ""
    url: str = ""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ForwardRule(BaseModel):
    enabled: bool = True
    project_name: str = Field(default="", validation_alias=AliasChoices("project_name", "upstream"))
    upstream_id: str = ""
    forward_id: str = Field(default_factory=generate_hash_id, validation_alias=AliasChoices("forward_id", "id"))
    from_path: str = Field(default="", alias="from")
    to_path: str = Field(default="", alias="to")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class MemoryEntry(BaseModel):
    memory_id: str = Field(default_factory=generate_hash_id)
    upstream_id: str = ""
    forward_id: str = ""
    project_name: str = ""
    from_path: str = Field(default="", alias="from")
    to_path: str = Field(default="", alias="to")
    last_synced: str = ""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class CommitMessages(BaseModel):
    upstreams: dict[str, str] = Field(
        default_factory=lambda: {"default": "sync: auto-update from {upstream_name} [{datetime}]"}
    )


class GitConfig(BaseModel):
    auto_commit: bool = Field(default_factory=lambda: Settings.GIT_AUTO_COMMIT)
    auto_push: bool = Field(default_factory=lambda: Settings.GIT_AUTO_PUSH)
    branch: str = Field(default_factory=lambda: Settings.GIT_BRANCH)
    commit_messages: CommitMessages = Field(default_factory=CommitMessages)


class ScheduleConfig(BaseModel):
    run_at: str | None = None
    interval_minutes: int = Field(default_factory=lambda: Settings.SYNC_INTERVAL_MINUTES, ge=1)
    poll_interval_seconds: int = Field(default_factory=lambda: Settings.SYNC_POLL_SECONDS, ge=1)


class AutomationConfig(BaseModel):
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    git: GitConfig = Field(default_factory=GitConfig)


class UpstreamConfigFile(BaseModel):
    upstreams: list[UpstreamEntry] = Field(default_factory=list)


class ForwardConfigFile(BaseModel):
    forwards: list[ForwardRule] = Field(default_factory=list)


class ConfigReloadDiff(BaseModel):
    upstreams_before: int
    upstreams_after: int
    forwards_before: int
    forwards_after: int
    schedule_changed: bool

    @property
    def has_changes(self) -> bool:
        return (
            self.upstreams_before != self.upstreams_after
            or self.forwards_before != self.forwards_after
            or self.schedule_changed
        )


class SyncResult(BaseModel):
    project_id: str = ""
    pull_results: dict[str, bool] = Field(default_factory=dict)
    updated_upstreams: list[str] = Field(default_factory=list)
    copied_targets: list[str] = Field(default_factory=list)
    removed_orphans: list[str] = Field(default_factory=list)
    committed_upstreams: list[str] = Field(default_factory=list)
    push_ok: bool = False


ProjectStatus = Literal["idle", "running", "error", "paused"]


class ProjectMeta(BaseModel):
    id: str
    name: str
    path: str
    status: ProjectStatus = "idle"
    last_sync: str | None = None
    created_at: str = ""
    updated_at: str = ""


class ProjectDetail(BaseModel):
    id: str
    name: str
    path: str
    status: ProjectStatus = "idle"
    last_sync: str | None = None
    created_at: str = ""
    updated_at: str = ""
    upstreams: list[UpstreamEntry] = Field(default_factory=list)
    forwards: list[ForwardRule] = Field(default_factory=list)
    git: GitConfig = Field(default_factory=GitConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    last_result: SyncResult | None = None


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)


class ProjectUpdate(BaseModel):
    upstreams: list[UpstreamEntry] | None = None
    forwards: list[ForwardRule] | None = None
    git: GitConfig | None = None
    schedule: ScheduleConfig | None = None


PROJECT_META_LIST_ADAPTER = TypeAdapter(list[ProjectMeta])
MEMORY_LIST_ADAPTER = TypeAdapter(list[MemoryEntry])
