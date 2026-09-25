from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass
class MediaItem:
    source_id: str
    kind: str
    page_url: str
    download_url: str
    width: int
    height: int
    duration: float
    creator: str
    tags: str

    @property
    def clip_id(self) -> str:
        return f"{self.kind}_{self.source_id}"


@dataclass
class Candidate:
    source: str
    source_id: str
    source_url: str
    download_url: str
    kind: str
    width: int = 0
    height: int = 0
    duration: float = 0.0
    creator: str = ""
    license: str = ""
    source_tags: str = ""
    thumbnail_url: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def clip_id(self) -> str:
        return f"{self.source}_{self.source_id}"


@dataclass
class SearchFilters:
    kind: str = "video"
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    orientation: Optional[str] = None
    min_width: Optional[int] = None
    per_page: int = 20
    page: int = 1


@runtime_checkable
class StockSource(Protocol):
    name: str

    def is_available(self) -> bool: ...
    def search(self, query: str, filters: SearchFilters) -> list[Candidate]: ...
    def download(self, candidate: Candidate, out_path: Path) -> Path: ...
