from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any


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
    views: int = 0
    downloads: int = 0
    likes: int = 0
    avg_color: str = ""
    aspect_ratio: str = ""
    score: float = 0.0

    @property
    def clip_id(self) -> str:
        return f"{self.kind}_{self.source_id}"

    def resolve_aspect_ratio(self) -> str:
        if self.width <= 0 or self.height <= 0:
            return "unknown"
        r = self.width / self.height
        if r >= 1.35:
            return "horizontal"
        if r <= 0.85:
            return "vertical"
        return "square"


def probe_media_metadata(path: Path, kind: str) -> tuple[int, int, float, str]:
    if not path.exists():
        return 0, 0, 0.0, "unknown"

    width, height, duration = 0, 0, 0.0

    if kind == "image":
        try:
            from PIL import Image
            with Image.open(path) as img:
                width, height = img.size
        except Exception:
            pass
    elif kind == "video":
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "json",
                str(path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                streams = data.get("streams", [])
                if streams:
                    s = streams[0]
                    width = int(s.get("width") or 0)
                    height = int(s.get("height") or 0)
                    duration = float(s.get("duration") or 0.0)
        except Exception:
            pass

    ratio = "unknown"
    if width > 0 and height > 0:
        r = width / height
        if r >= 1.35:
            ratio = "horizontal"
        elif r <= 0.85:
            ratio = "vertical"
        else:
            ratio = "square"

    return width, height, duration, ratio


def save_manifest(output_dir: Path, query: str, provider: str, items: list[dict[str, Any]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest_data = {
        "query": query,
        "provider": provider,
        "total_items": len(items),
        "items": items,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path
