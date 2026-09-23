from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
import requests

from .base import MediaItem

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
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        params: dict[str, Any] = {
            "query": query,
            "per_page": max(1, min(per_page, 80)),
            "page": max(1, page),
        }
        if orientation:
            params["orientation"] = orientation

        resp = requests.get(self.image_endpoint, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        photos = resp.json().get("photos", []) or []

        items: list[MediaItem] = []
        for p in photos:
            src = p.get("src", {})
            download_url = src.get(image_format) or src.get("large2x") or src.get("original", "")
            if not download_url:
                continue
            items.append(
                MediaItem(
                    source_id=str(p.get("id")),
                    kind="image",
                    page_url=p.get("url", "") or "",
                    download_url=download_url,
                    width=int(p.get("width") or 0),
                    height=int(p.get("height") or 0),
                    duration=0.0,
                    creator=p.get("photographer", "") or "",
                    tags=p.get("alt", "") or "",
                )
            )
        return items

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        video_format: str = "hd",
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        orientation: Optional[str] = None,
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        params: dict[str, Any] = {
            "query": query,
            "per_page": max(1, min(per_page, 80)),
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

            items.append(
                MediaItem(
                    source_id=str(v.get("id")),
                    kind="video",
                    page_url=v.get("url", "") or "",
                    download_url=rend["link"],
                    width=int(rend.get("width") or 0),
                    height=int(rend.get("height") or 0),
                    duration=duration,
                    creator=v.get("user", {}).get("name", "") or "",
                    tags="",
                )
            )
        return items

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

    client = PexelsSource()
    if not client.api_key:
        return {"success": False, "error": "Missing PEXELS_API_KEY"}

    downloaded: dict[str, list[str]] = {"videos": [], "images": []}
    errors: list[str] = []

    try:
        if video_count:
            videos = client.search_videos(query, per_page=max(1, video_count), video_format=video_format)
            for item in videos[:video_count]:
                try:
                    path = client.download(item, output_dir)
                    downloaded["videos"].append(str(path))
                except Exception as exc:
                    errors.append(f"video {item.source_id}: {exc}")

        if image_count:
            images = client.search_images(query, per_page=max(1, image_count), image_format=image_format)
            for item in images[:image_count]:
                try:
                    path = client.download(item, output_dir)
                    downloaded["images"].append(str(path))
                except Exception as exc:
                    errors.append(f"image {item.source_id}: {exc}")

        return {
            "success": bool(downloaded["videos"] or downloaded["images"]),
            "query": query,
            "output_dir": str(output_dir),
            "downloaded": downloaded,
            "errors": errors,
        }
    except Exception as exc:
        return {"success": False, "error": f"Pexels search failed: {exc}"}
