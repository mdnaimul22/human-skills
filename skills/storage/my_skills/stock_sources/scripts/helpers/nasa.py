from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
from typing import Any, Optional
from urllib.parse import quote, urlparse, urlunparse
import requests

from .base import Candidate, MediaItem, SearchFilters, probe_media_metadata, save_manifest

_SEARCH_URL = "https://images-api.nasa.gov/search"
_UNSAFE_ID_CHARS = re.compile(r"[^A-Za-z0-9._\-]+")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Connection": "close",
}


def _sanitize_source_id(raw: str) -> str:
    if not raw:
        return "unknown"
    cleaned = _UNSAFE_ID_CHARS.sub("_", raw.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_.")
    if not cleaned:
        return "unknown"
    return cleaned[:120]


def _encode_url_path(url: str) -> str:
    try:
        parts = urlparse(url)
    except Exception:
        return url
    safe_path = quote(parts.path, safe="/")
    return urlunparse(parts._replace(path=safe_path))


def _pick_video_url(file_urls: list[str]) -> str:
    priority = ("orig", "large", "medium", "small")
    buckets: dict[str, list[str]] = {p: [] for p in priority}
    for url in file_urls:
        lower = url.lower()
        if not lower.endswith((".mp4", ".mov", ".m4v")):
            continue
        for p in priority:
            if f"~{p}." in lower:
                buckets[p].append(url)
                break
    for p in priority:
        if buckets[p]:
            return buckets[p][0]
    for url in file_urls:
        if url.lower().endswith(".mp4"):
            return url
    return ""


def _pick_image_url(file_urls: list[str]) -> str:
    priority = ("orig", "large", "medium")
    buckets: dict[str, list[str]] = {p: [] for p in priority}
    for url in file_urls:
        lower = url.lower()
        if not lower.endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
            continue
        for p in priority:
            if f"~{p}." in lower:
                buckets[p].append(url)
                break
    for p in priority:
        if buckets[p]:
            return buckets[p][0]
    for url in file_urls:
        if url.lower().endswith((".jpg", ".jpeg", ".png")):
            return url
    return ""


class NasaSource:
    name = "nasa"
    display_name = "NASA"
    provider = "nasa"
    priority = 30
    supports = {"video": True, "image": True}

    def is_available(self) -> bool:
        return True

    def _hydrate_media_item(
        self,
        item_data: dict,
        media_type: str,
        aspect_ratio: Optional[str] = None,
    ) -> Optional[MediaItem]:
        data_list = item_data.get("data") or []
        if not data_list:
            return None
        meta = data_list[0]

        nasa_id = meta.get("nasa_id")
        m_type = (meta.get("media_type") or "").lower()
        if not nasa_id or m_type != media_type:
            return None

        asset_href = item_data.get("href")
        if not asset_href:
            return None

        try:
            r = requests.get(asset_href, headers=_HEADERS, timeout=20)
            r.raise_for_status()
            file_urls = r.json()
        except Exception:
            return None

        if not isinstance(file_urls, list) or not file_urls:
            return None

        if media_type == "video":
            download_url = _pick_video_url(file_urls)
        else:
            download_url = _pick_image_url(file_urls)

        if not download_url:
            return None
        download_url = _encode_url_path(download_url)

        title = (meta.get("title") or "").strip()
        description = (meta.get("description") or "").strip()
        keywords = meta.get("keywords") or []
        kw_text = " ".join(str(k) for k in keywords if k) if isinstance(keywords, list) else str(keywords)
        tags = " ".join(s for s in (title, description, kw_text) if s).strip()[:500]

        creator = (meta.get("photographer") or meta.get("center") or "").strip()
        safe_id = _sanitize_source_id(nasa_id)

        item = MediaItem(
            source_id=safe_id,
            kind=media_type,
            page_url=f"https://images.nasa.gov/details/{quote(nasa_id, safe='')}",
            download_url=download_url,
            width=0,
            height=0,
            duration=0.0,
            creator=creator,
            tags=tags,
            score=10.0,
        )
        item.aspect_ratio = "unknown"
        return item

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        params = [
            ("q", query),
            ("media_type", "image"),
            ("page_size", str(max(1, min(per_page * 2, 50)))),
            ("page", str(max(1, page))),
        ]
        try:
            r = requests.get(_SEARCH_URL, params=params, headers=_HEADERS, timeout=25)
            r.raise_for_status()
            raw_items = ((r.json().get("collection") or {}).get("items") or [])
        except Exception:
            return []

        items: list[MediaItem] = []
        for raw in raw_items:
            it = self._hydrate_media_item(raw, "image", aspect_ratio=aspect_ratio)
            if it:
                items.append(it)
            if len(items) >= per_page:
                break
        return items[:per_page]

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        params = [
            ("q", query),
            ("media_type", "video"),
            ("page_size", str(max(1, min(per_page * 2, 50)))),
            ("page", str(max(1, page))),
        ]
        try:
            r = requests.get(_SEARCH_URL, params=params, headers=_HEADERS, timeout=25)
            r.raise_for_status()
            raw_items = ((r.json().get("collection") or {}).get("items") or [])
        except Exception:
            return []

        items: list[MediaItem] = []
        for raw in raw_items:
            it = self._hydrate_media_item(raw, "video", aspect_ratio=aspect_ratio)
            if it:
                items.append(it)
            if len(items) >= per_page:
                break
        return items[:per_page]

    def search(self, query: str, filters: SearchFilters) -> list[Candidate]:
        kind = (filters.kind or "video").lower()
        items: list[MediaItem] = []
        if kind in ("video", "any"):
            items.extend(self.search_videos(query, per_page=filters.per_page, page=filters.page))
        if kind in ("image", "any") and len(items) < filters.per_page:
            items.extend(self.search_images(query, per_page=filters.per_page - len(items), page=filters.page))

        candidates: list[Candidate] = []
        for it in items:
            candidates.append(
                Candidate(
                    source=self.name,
                    source_id=it.source_id,
                    source_url=it.page_url,
                    download_url=it.download_url,
                    kind=it.kind,
                    width=it.width,
                    height=it.height,
                    duration=it.duration,
                    creator=it.creator,
                    source_tags=it.tags,
                    thumbnail_url=it.download_url,
                )
            )
        return candidates

    def download(self, item: Any, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        kind = getattr(item, "kind", "media")
        source_id = getattr(item, "source_id", getattr(item, "clip_id", "item"))
        download_url = item.download_url
        suffix = Path(urlparse(download_url).path).suffix or (".mp4" if kind == "video" else ".jpg")
        target = out_dir / f"{kind}_{source_id}{suffix}"

        with requests.get(download_url, headers=_HEADERS, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return target


def search_nasa(inputs: dict[str, Any]) -> dict[str, Any]:
    query = inputs["query"]
    output_dir = Path(inputs.get("output_dir", "downloads")) / query.replace(" ", "_")
    video_count = max(0, int(inputs.get("video_count", 0)))
    image_count = max(0, int(inputs.get("image_count", 0)))
    if video_count == 0 and image_count == 0:
        video_count = 2

    aspect_ratio = inputs.get("aspect_ratio")
    max_workers = max(1, min(int(inputs.get("concurrent_downloads", 4)), 8))

    client = NasaSource()
    downloaded: dict[str, list[str]] = {"videos": [], "images": []}
    manifest_items: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        targets: list[MediaItem] = []
        if video_count:
            videos = client.search_videos(query, per_page=video_count, aspect_ratio=aspect_ratio)
            targets.extend(videos)

        if image_count:
            images = client.search_images(query, per_page=image_count, aspect_ratio=aspect_ratio)
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
                    if path.exists() and (item.width <= 0 or item.height <= 0):
                        pw, ph, pdur, pratio = probe_media_metadata(path, item.kind)
                        item.width = pw or item.width
                        item.height = ph or item.height
                        item.duration = pdur or item.duration
                        item.aspect_ratio = pratio

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
                        "tags": item.tags,
                    })

        manifest_path = None
        if manifest_items:
            manifest_path = save_manifest(output_dir, query, "nasa", manifest_items)

        return {
            "success": bool(downloaded["videos"] or downloaded["images"]),
            "query": query,
            "provider": "nasa",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path) if manifest_path else "",
            "downloaded": downloaded,
            "items_count": len(manifest_items),
            "errors": errors,
        }
    except Exception as exc:
        return {"success": False, "error": f"NASA search failed: {exc}"}
