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

_VIDEO_TIERS = ["large", "medium", "small", "tiny"]
_IMAGE_FORMATS = {
    "large": "largeImageURL",
    "webformat": "webformatURL",
    "preview": "previewURL",
}


def _calc_score(likes: int, downloads: int, views: int) -> float:
    return round((likes * 3.0) + (downloads * 1.5) + (views * 0.05), 2)


class PixabaySource:
    name = "pixabay"
    display_name = "Pixabay"
    provider = "pixabay"
    priority = 15
    supports = {"video": True, "image": True}

    def __init__(self):
        self.api_key = Settings.PIXABAY_API_KEY
        self.base_url = Settings.PIXABAY_API_URL.rstrip("/")
        self.image_endpoint = self.base_url
        self.video_endpoint = f"{self.base_url}/videos/"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        image_format: str = "large",
        orientation: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        colors: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        url_field = _IMAGE_FORMATS.get(image_format, "largeImageURL")
        params: dict[str, Any] = {
            "key": self.api_key,
            "q": query,
            "per_page": max(3, min(per_page * 3, 200)),
            "page": max(1, page),
            "safesearch": "true",
        }
        if orientation:
            params["orientation"] = orientation
        if colors:
            params["colors"] = colors
        if category:
            params["category"] = category

        resp = requests.get(self.image_endpoint, params=params, timeout=30)
        resp.raise_for_status()
        hits = resp.json().get("hits", []) or []

        items: list[MediaItem] = []
        for h in hits:
            download_url = h.get(url_field) or h.get("largeImageURL") or h.get("webformatURL", "")
            if not download_url:
                continue

            likes = int(h.get("likes") or 0)
            downloads = int(h.get("downloads") or 0)
            views = int(h.get("views") or 0)
            score = _calc_score(likes, downloads, views)

            item = MediaItem(
                source_id=str(h.get("id")),
                kind="image",
                page_url=h.get("pageURL", "") or "",
                download_url=download_url,
                width=int(h.get("imageWidth") or 0),
                height=int(h.get("imageHeight") or 0),
                duration=0.0,
                creator=h.get("user", "") or "",
                tags=h.get("tags", "") or "",
                views=views,
                downloads=downloads,
                likes=likes,
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
        video_format: str = "large",
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        params: dict[str, Any] = {
            "key": self.api_key,
            "q": query,
            "per_page": max(3, min(per_page * 3, 200)),
            "page": max(1, page),
            "safesearch": "true",
        }
        if min_duration is not None:
            params["min_duration"] = int(min_duration)
        if max_duration is not None:
            params["max_duration"] = int(max_duration)
        if category:
            params["category"] = category

        resp = requests.get(self.video_endpoint, params=params, timeout=30)
        resp.raise_for_status()
        hits = resp.json().get("hits", []) or []

        start_idx = _VIDEO_TIERS.index(video_format) if video_format in _VIDEO_TIERS else 0
        tiers = _VIDEO_TIERS[start_idx:] + _VIDEO_TIERS[:start_idx]

        items: list[MediaItem] = []
        for h in hits:
            duration = float(h.get("duration", 0) or 0)
            if min_duration is not None and duration < min_duration:
                continue
            if max_duration is not None and duration > max_duration:
                continue

            videos = h.get("videos", {})
            rend = None
            for tier in tiers:
                candidate = videos.get(tier)
                if candidate and candidate.get("url"):
                    rend = candidate
                    break
            if not rend:
                continue

            likes = int(h.get("likes") or 0)
            downloads = int(h.get("downloads") or 0)
            views = int(h.get("views") or 0)
            score = _calc_score(likes, downloads, views)

            item = MediaItem(
                source_id=str(h.get("id")),
                kind="video",
                page_url=h.get("pageURL", "") or "",
                download_url=rend["url"],
                width=int(rend.get("width") or 0),
                height=int(rend.get("height") or 0),
                duration=duration,
                creator=h.get("user", "") or "",
                tags=h.get("tags", "") or "",
                views=views,
                downloads=downloads,
                likes=likes,
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


def search_pixabay(inputs: dict[str, Any]) -> dict[str, Any]:
    query = inputs["query"]
    output_dir = Path(inputs.get("output_dir", "downloads")) / query.replace(" ", "_")
    video_count = max(0, int(inputs.get("video_count", 5)))
    image_count = max(0, int(inputs.get("image_count", 5)))
    video_format = inputs.get("video_format", "large")
    image_format = inputs.get("image_format", "large")
    aspect_ratio = inputs.get("aspect_ratio")
    min_duration = inputs.get("min_duration")
    max_duration = inputs.get("max_duration")
    colors = inputs.get("colors")
    category = inputs.get("category")
    max_workers = max(1, min(int(inputs.get("concurrent_downloads", 6)), 12))

    client = PixabaySource()
    if not client.api_key:
        return {"success": False, "error": "Missing PIXABAY_API_KEY"}

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
                aspect_ratio=aspect_ratio,
                category=category,
            )
            targets.extend(videos)

        if image_count:
            images = client.search_images(
                query,
                per_page=image_count,
                image_format=image_format,
                aspect_ratio=aspect_ratio,
                colors=colors,
                category=category,
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
                        "views": item.views,
                        "downloads": item.downloads,
                        "likes": item.likes,
                        "popularity_score": item.score,
                        "tags": item.tags,
                    })

        manifest_path = None
        if manifest_items:
            manifest_path = save_manifest(output_dir, query, "pixabay", manifest_items)

        return {
            "success": bool(downloaded["videos"] or downloaded["images"]),
            "query": query,
            "provider": "pixabay",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path) if manifest_path else "",
            "downloaded": downloaded,
            "items_count": len(manifest_items),
            "errors": errors,
        }
    except Exception as exc:
        return {"success": False, "error": f"Pixabay search failed: {exc}"}