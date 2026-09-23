from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
import requests

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


class PixabaySource:

    def __init__(self):
        self.api_key = Settings.PIXABAY_API_KEY
        self.base_url = Settings.PIXABAY_API_URL.rstrip("/")
        self.image_endpoint = self.base_url
        self.video_endpoint = f"{self.base_url}/videos/"

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        image_format: str = "large",
        orientation: Optional[str] = None,
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        url_field = _IMAGE_FORMATS.get(image_format, "largeImageURL")

        params: dict[str, Any] = {
            "key": self.api_key,
            "q": query,
            "per_page": max(3, min(per_page, 200)),
            "page": max(1, page),
            "safesearch": "true",
        }
        if orientation:
            params["orientation"] = orientation

        resp = requests.get(self.image_endpoint, params=params, timeout=30)
        resp.raise_for_status()
        hits = resp.json().get("hits", []) or []

        items: list[MediaItem] = []
        for h in hits:
            download_url = h.get(url_field) or h.get("largeImageURL") or h.get("webformatURL", "")
            if not download_url:
                continue
            items.append(
                MediaItem(
                    source_id=str(h.get("id")),
                    kind="image",
                    page_url=h.get("pageURL", "") or "",
                    download_url=download_url,
                    width=int(h.get("imageWidth") or 0),
                    height=int(h.get("imageHeight") or 0),
                    duration=0.0,
                    creator=h.get("user", "") or "",
                    tags=h.get("tags", "") or "",
                )
            )
        return items

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        video_format: str = "large",
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
    ) -> list[MediaItem]:
        if not self.api_key:
            return []

        params: dict[str, Any] = {
            "key": self.api_key,
            "q": query,
            "per_page": max(3, min(per_page, 200)),
            "page": max(1, page),
            "safesearch": "true",
        }
        if min_duration is not None:
            params["min_duration"] = int(min_duration)
        if max_duration is not None:
            params["max_duration"] = int(max_duration)

        resp = requests.get(self.video_endpoint, params=params, timeout=30)
        resp.raise_for_status()
        hits = resp.json().get("hits", []) or []

        start_idx = _VIDEO_TIERS.index(video_format) if video_format in _VIDEO_TIERS else 0
        tiers = _VIDEO_TIERS[start_idx:] + _VIDEO_TIERS[:start_idx]

        items: list[MediaItem] = []
        for h in hits:
            videos = h.get("videos", {})
            rend = None
            for tier in tiers:
                candidate = videos.get(tier)
                if candidate and candidate.get("url"):
                    rend = candidate
                    break
            if not rend:
                continue
            items.append(
                MediaItem(
                    source_id=str(h.get("id")),
                    kind="video",
                    page_url=h.get("pageURL", "") or "",
                    download_url=rend["url"],
                    width=int(rend.get("width") or 0),
                    height=int(rend.get("height") or 0),
                    duration=float(h.get("duration", 0) or 0),
                    creator=h.get("user", "") or "",
                    tags=h.get("tags", "") or "",
                )
            )
        return items

    def download(self, item: MediaItem, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(urlparse(item.download_url).path).suffix or (".mp4" if item.kind == "video" else ".jpg")
        target = out_dir / f"{item.kind}_{item.source_id}{suffix}"

        with requests.get(item.download_url, stream=True, timeout=120) as r:
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

    client = PixabaySource()
    if not client.api_key:
        return {"success": False, "error": "Missing PIXABAY_API_KEY"}

    downloaded: dict[str, list[str]] = {"videos": [], "images": []}
    errors: list[str] = []

    try:
        if video_count:
            videos = client.search_videos(query, per_page=max(3, video_count), video_format=video_format)
            for item in videos[:video_count]:
                try:
                    path = client.download(item, output_dir)
                    downloaded["videos"].append(str(path))
                except Exception as exc:
                    errors.append(f"video {item.source_id}: {exc}")

        if image_count:
            images = client.search_images(query, per_page=max(3, image_count), image_format=image_format)
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
        return {"success": False, "error": f"Pixabay search failed: {exc}"}