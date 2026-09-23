from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
import requests

from .base import MediaItem, save_manifest

try:
    from helpers.settings import Settings
    from helpers.dotenv import load_dotenv
except ImportError:
    from skills.helpers.settings import Settings
    from skills.helpers.dotenv import load_dotenv

load_dotenv()

_VIDEO_QUALITIES = ["hd", "sd"]
_IMAGE_SIZES = ["large2x", "large", "medium", "small", "original"]


class PexelsSource:
    name = "pexels"
    display_name = "Pexels"
    provider = "pexels"
    priority = 10
    supports = {"video": True, "image": True}

    def __init__(self):
        self.api_key = Settings.PEXELS_API_KEY
        self.base_url = Settings.PEXELS_API_URL.rstrip("/")
        self.image_endpoint = f"{self.base_url}/v1/search"
        self.video_endpoint = f"{self.base_url}/videos/search"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": self.api_key} if self.api_key else {}

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        image_format: str = "large2x",
        orientation: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        color: Optional[str] = None,
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        params: dict[str, Any] = {
            "query": query,
            "per_page": max(1, min(per_page * 3, 80)),
            "page": max(1, page),
        }
        if orientation:
            params["orientation"] = orientation
        if color:
            params["color"] = color

        resp = requests.get(self.image_endpoint, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        photos = resp.json().get("photos", []) or []

        items: list[MediaItem] = []
        for p in photos:
            src = p.get("src", {})
            download_url = src.get(image_format) or src.get("large2x") or src.get("original", "")
            if not download_url:
                continue

            width = int(p.get("width") or 0)
            height = int(p.get("height") or 0)
            score = round((width * height) / 1000000.0, 2)

            item = MediaItem(
                source_id=str(p.get("id")),
                kind="image",
                page_url=p.get("url", "") or "",
                download_url=download_url,
                width=width,
                height=height,
                duration=0.0,
                creator=p.get("photographer", "") or "",
                tags=p.get("alt", "") or "",
                avg_color=p.get("avg_color", ""),
                score=score,
            )
            item.aspect_ratio = item.resolve_aspect_ratio()
            if aspect_ratio and item.aspect_ratio != aspect_ratio:
                continue
            items.append(item)

        items.sort(key=lambda x: x.score, reverse=True)
        return items[:per_page]

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        video_format: str = "hd",
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        orientation: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        params: dict[str, Any] = {
            "query": query,
            "per_page": max(1, min(per_page * 3, 80)),
            "page": max(1, page),
        }
        if orientation:
            params["orientation"] = orientation

        resp = requests.get(self.video_endpoint, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        videos = resp.json().get("videos", []) or []

        items: list[MediaItem] = []
        for v in videos:
            duration = float(v.get("duration", 0) or 0)
            if min_duration is not None and duration < min_duration:
                continue
            if max_duration is not None and duration > max_duration:
                continue

            video_files = v.get("video_files", []) or []
            rend = None
            for vf in sorted(video_files, key=lambda x: int(x.get("width") or 0), reverse=True):
                if vf.get("quality") == video_format:
                    rend = vf
                    break
            if not rend and video_files:
                rend = max(video_files, key=lambda x: int(x.get("width") or 0))

            if not rend or not rend.get("link"):
                continue

            width = int(rend.get("width") or 0)
            height = int(rend.get("height") or 0)
            fps = float(rend.get("fps") or 30.0)
            score = round((width * height * fps) / 1000000.0, 2)

            item = MediaItem(
                source_id=str(v.get("id")),
                kind="video",
                page_url=v.get("url", "") or "",
                download_url=rend["link"],
                width=width,
                height=height,
                duration=duration,
                creator=v.get("user", {}).get("name", "") or "",
                tags="",
                score=score,
            )
            item.aspect_ratio = item.resolve_aspect_ratio()
            if aspect_ratio and item.aspect_ratio != aspect_ratio:
                continue
            items.append(item)

        items.sort(key=lambda x: x.score, reverse=True)
        return items[:per_page]

    def search(self, query: str, filters: Any) -> list[MediaItem]:
        kind = getattr(filters, "kind", "any") or "any"
        results: list[MediaItem] = []
        if kind in ("video", "any"):
            results.extend(
                self.search_videos(
                    query,
                    per_page=getattr(filters, "per_page", 5),
                    page=getattr(filters, "page", 1),
                )
            )
        if kind in ("image", "any"):
            results.extend(
                self.search_images(
                    query,
                    per_page=getattr(filters, "per_page", 5),
                    page=getattr(filters, "page", 1),
                )
            )
        return results

    def download(self, item: Any, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        kind = getattr(item, "kind", "media")
        source_id = getattr(item, "source_id", getattr(item, "clip_id", "item"))
        download_url = item.download_url
        suffix = Path(urlparse(download_url).path).suffix or (".mp4" if kind == "video" else ".jpg")
        target = out_dir / f"{kind}_{source_id}{suffix}"

        with requests.get(download_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return target


def search_pexels(inputs: dict[str, Any]) -> dict[str, Any]:
    query = inputs["query"]
    output_dir = Path(inputs.get("output_dir", "downloads")) / query.replace(" ", "_")
    video_count = max(0, int(inputs.get("video_count", 5)))
    image_count = max(0, int(inputs.get("image_count", 5)))
    video_format = inputs.get("video_format", "hd")
    image_format = inputs.get("image_format", "large2x")
    aspect_ratio = inputs.get("aspect_ratio")
    min_duration = inputs.get("min_duration")
    max_duration = inputs.get("max_duration")
    color = inputs.get("color")
    orientation = inputs.get("orientation")
    max_workers = max(1, min(int(inputs.get("concurrent_downloads", 6)), 12))

    client = PexelsSource()
    if not client.api_key:
        return {"success": False, "error": "Missing PEXELS_API_KEY"}

    downloaded: dict[str, list[str]] = {"videos": [], "images": []}
    manifest_items: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        targets: list[MediaItem] = []
        if video_count:
            videos = client.search_videos(
                query,
                per_page=video_count,
                video_format=video_format,
                min_duration=min_duration,
                max_duration=max_duration,
                orientation=orientation,
                aspect_ratio=aspect_ratio,
            )
            targets.extend(videos)

        if image_count:
            images = client.search_images(
                query,
                per_page=image_count,
                image_format=image_format,
                orientation=orientation,
                aspect_ratio=aspect_ratio,
                color=color,
            )
            targets.extend(images)

        def _fetch(item: MediaItem) -> tuple[MediaItem, Optional[Path], Optional[str]]:
            try:
                sub_dir = output_dir / ("videos" if item.kind == "video" else "images")
                dest = client.download(item, sub_dir)
                return item, dest, None
            except Exception as exc:
                return item, None, str(exc)

        if targets:
            with ThreadPoolExecutor(max_workers=min(len(targets), max_workers)) as executor:
                futures = [executor.submit(_fetch, it) for it in targets]
                for future in as_completed(futures):
                    item, path, err = future.result()
                    if err or not path:
                        errors.append(f"{item.kind} {item.source_id}: {err}")
                        continue

                    if item.kind == "video":
                        downloaded["videos"].append(str(path))
                    else:
                        downloaded["images"].append(str(path))

                    size_bytes = path.stat().st_size if path.exists() else 0
                    manifest_items.append({
                        "file_name": path.name,
                        "file_path": str(path),
                        "kind": item.kind,
                        "source_id": item.source_id,
                        "resolution": f"{item.width}x{item.height}",
                        "aspect_ratio": item.aspect_ratio,
                        "duration_seconds": item.duration,
                        "file_size_bytes": size_bytes,
                        "file_size_mb": round(size_bytes / (1024 * 1024), 2),
                        "creator": item.creator,
                        "page_url": item.page_url,
                        "download_url": item.download_url,
                        "avg_color": item.avg_color,
                        "quality_score": item.score,
                        "tags": item.tags,
                    })

        manifest_path = None
        if manifest_items:
            manifest_path = save_manifest(output_dir, query, "pexels", manifest_items)

        return {
            "success": bool(downloaded["videos"] or downloaded["images"]),
            "query": query,
            "provider": "pexels",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path) if manifest_path else "",
            "downloaded": downloaded,
            "items_count": len(manifest_items),
            "errors": errors,
        }
    except Exception as exc:
        return {"success": False, "error": f"Pexels search failed: {exc}"}
