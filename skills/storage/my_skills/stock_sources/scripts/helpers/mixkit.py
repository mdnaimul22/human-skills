from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests

from .base import Candidate, MediaItem, SearchFilters, probe_media_metadata, save_manifest

_BASE_URL = "https://mixkit.co"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Connection": "close",
}


class MixkitSource:
    name = "mixkit"
    display_name = "Mixkit"
    provider = "mixkit"
    priority = 19
    supports = {"video": True, "image": False}

    def is_available(self) -> bool:
        return True

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        slug = query.lower().strip().replace(" ", "-")
        search_url = f"{_BASE_URL}/free-stock-video/{slug}/"

        try:
            r = requests.get(search_url, headers=_HEADERS, timeout=20)
            if r.status_code == 404:
                search_url = f"{_BASE_URL}/free-stock-video/"
                r = requests.get(search_url, headers=_HEADERS, timeout=20)
            r.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".item-grid__item, .video-item, article, [class*='item-grid']")
        items: list[MediaItem] = []
        seen_ids = set()

        for card in cards:
            video_el = card.select_one("video")
            if not video_el:
                continue

            src = video_el.get("src") or ""
            if not src:
                continue

            hd_src = src.replace("-360.mp4", "-720.mp4")

            title_el = card.select_one("h2, h3, [class*='title'], a")
            title = title_el.get_text(strip=True) if title_el else ""

            link_el = card.select_one("a[href]")
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                page_url = f"{_BASE_URL}{href}"
            else:
                page_url = href or search_url

            parsed = urlparse(src).path
            clip_id = Path(parsed).stem.split("-")[0]
            if clip_id in seen_ids:
                continue
            seen_ids.add(clip_id)

            item = MediaItem(
                source_id=clip_id,
                kind="video",
                page_url=page_url,
                download_url=hd_src,
                width=1280,
                height=720,
                duration=0.0,
                creator="Mixkit / Envato",
                tags=f"{title} {query}".strip(),
                score=10.0,
            )
            item.aspect_ratio = item.resolve_aspect_ratio()

            if aspect_ratio and item.aspect_ratio != aspect_ratio:
                continue

            items.append(item)
            if len(items) >= per_page:
                break

        return items[:per_page]

    def search(self, query: str, filters: SearchFilters) -> list[Candidate]:
        kind = (filters.kind or "video").lower()
        if kind == "image":
            return []

        media_items = self.search_videos(
            query=query,
            per_page=filters.per_page,
            min_duration=filters.min_duration,
            max_duration=filters.max_duration,
            aspect_ratio=filters.orientation,
        )

        candidates: list[Candidate] = []
        for it in media_items:
            candidates.append(
                Candidate(
                    source=self.name,
                    source_id=it.source_id,
                    source_url=it.page_url,
                    download_url=it.download_url,
                    kind="video",
                    width=it.width,
                    height=it.height,
                    duration=it.duration,
                    creator=it.creator,
                    source_tags=it.tags,
                    thumbnail_url=it.download_url.replace("-720.mp4", "-thumb.jpg"),
                )
            )
        return candidates

    def download(self, item: Any, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        kind = getattr(item, "kind", "video")
        source_id = getattr(item, "source_id", getattr(item, "clip_id", "clip"))
        download_url = item.download_url
        suffix = Path(urlparse(download_url).path).suffix or ".mp4"
        target = out_dir / f"{kind}_{source_id}{suffix}"

        try:
            with requests.get(download_url, headers=_HEADERS, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(target, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 16):
                        if chunk:
                            f.write(chunk)
            return target
        except Exception:
            fallback_url = download_url.replace("-720.mp4", "-360.mp4")
            with requests.get(fallback_url, headers=_HEADERS, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(target, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 16):
                        if chunk:
                            f.write(chunk)
            return target


def search_mixkit(inputs: dict[str, Any]) -> dict[str, Any]:
    query = inputs["query"]
    output_dir = Path(inputs.get("output_dir", "downloads")) / query.replace(" ", "_")
    video_count = max(0, int(inputs.get("video_count", 2)))
    aspect_ratio = inputs.get("aspect_ratio")
    min_duration = inputs.get("min_duration")
    max_duration = inputs.get("max_duration")
    max_workers = max(1, min(int(inputs.get("concurrent_downloads", 4)), 8))

    client = MixkitSource()
    downloaded: dict[str, list[str]] = {"videos": [], "images": []}
    manifest_items: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        targets: list[MediaItem] = []
        if video_count:
            videos = client.search_videos(
                query,
                per_page=video_count,
                min_duration=float(min_duration) if min_duration is not None else None,
                max_duration=float(max_duration) if max_duration is not None else None,
                aspect_ratio=aspect_ratio,
            )
            targets.extend(videos)

        def _fetch(item: MediaItem) -> tuple[MediaItem, Optional[Path], Optional[str]]:
            try:
                sub_dir = output_dir / "videos"
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

                    downloaded["videos"].append(str(path))
                    size_bytes = path.stat().st_size if path.exists() else 0

                    if path.exists():
                        pw, ph, pdur, pratio = probe_media_metadata(path, "video")
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
            manifest_path = save_manifest(output_dir, query, "mixkit", manifest_items)

        return {
            "success": bool(downloaded["videos"]),
            "query": query,
            "provider": "mixkit",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path) if manifest_path else "",
            "downloaded": downloaded,
            "items_count": len(manifest_items),
            "errors": errors,
        }
    except Exception as exc:
        return {"success": False, "error": f"Mixkit search failed: {exc}"}
