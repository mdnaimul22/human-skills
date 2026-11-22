from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, TypeAdapter

class ContainerStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    MISSING = "missing"
    FAILED = "failed"
    UNKNOWN = "unknown"

class ContainerSpec(BaseModel):
    name: str = Field(..., min_length=1)
    image: str = Field(..., min_length=1)
    port: Optional[int] = None
    host_port: Optional[int] = None
    bind_ip: str = "127.0.0.1"
    network_mode: str = "bridge"
    restart_policy: str = "always"
    command: Optional[str] = None
    environment: dict[str, str] = Field(default_factory=dict)
    volumes: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    background_pull: bool = False

class ContainerState(BaseModel):
    name: str
    status: ContainerStatus
    port_open: bool
    is_running: bool
    details: str = ""

CONTAINER_SPECS_ADAPTER: TypeAdapter[list[ContainerSpec]] = TypeAdapter(list[ContainerSpec])
CONTAINER_SPEC_ADAPTER: TypeAdapter[ContainerSpec] = TypeAdapter(ContainerSpec)
