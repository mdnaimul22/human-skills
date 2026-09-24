from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import html
from pathlib import Path
import re
from typing import Any, Optional
from urllib.parse import urlparse
import requests

from .base import Candidate, MediaItem, SearchFilters, save_manifest

_API_URL = "https://commons.wikimedia.org/w/api.php"
_USER_AGENT = "HumanSkillsStockCollector/1.0 (contact@human-skills.local)"
_COMMONS_LICENSE = "Wikimedia Commons (verify per-file license)"
_HTML_TAG_RE = re.compile(r"<[^>]+>")

_STOP_WORDS = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "into",
    "its", "their", "about", "over", "under", "while", "during",
    "your", "you", "our", "are", "was", "were", "have", "has",
})

_SOURCE_HINT_TOKENS = frozenset({
    "prelinger", "archive", "archives", "stock", "footage", "wikimedia", "commons",
})


def _looks_like_year(token: str) -> bool:
    bare = token.rstrip("s")
    return bare.isdigit() and len(bare) == 4


def _meta_value(meta: dict[str, Any], key: str) -> str:
    raw = ((meta.get(key) or {}).get("value")) or ""
    if not raw:
        return ""
    text = html.unescape(str(raw))
    text = _HTML_TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _build_search_queries(query: str, kind: str) -> list[tuple[str, str]]:
    user_query = query.strip()
    kind_l = (kind or "video").lower()
    prefix = "filetype:video" if kind_l == "video" else ("filetype:bitmap" if kind_l == "image" else "")

    def _wrap(text: str) -> str:
        return f"{prefix} {text}".strip() if prefix else text

    if not user_query:
        return [("default", _wrap(""))]

    tokens = [
        t for t in user_query.split()
        if len(t) >= 3
        and t.lower() not in _STOP_WORDS
        and t.lower() not in _SOURCE_HINT_TOKENS
    ]
    non_year = [t for t in tokens if not _looks_like_year(t)]

    queries: list[tuple[str, str]] = [("full", _wrap(user_query))]

    if len(non_year) >= 2:
        top2 = sorted(non_year, key=lambda t: -len(t))[:2]
        queries.append(("top2_or", _wrap(f"{top2[0]} {top2[1]}")))

    if non_year:
        best = max(non_year, key=len)
        queries.append(("single_best", _wrap(best)))

    return queries


class WikimediaSource:
    name = "wikimedia"
    display_name = "Wikimedia Commons"
    provider = "wikimedia"
    priority = 25
    supports = {"video": True, "image": True}

    def is_available(self) -> bool:
        return True

    def _search_media(
        self,
        query: str,
        kind: str,
        per_page: int = 5,
        page: int = 1,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        items: list[MediaItem] = []

        for _label, search_text in _build_search_queries(query, kind):
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": search_text,
                "gsrnamespace": 6,
                "gsrlimit": max(1, min(per_page * 3, 50)),
                "gsroffset": max(0, (max(page, 1) - 1) * max(1, min(per_page * 3, 50))),
                "prop": "imageinfo|info",
                "iiprop": "url|size|mime|extmetadata|mediatype",
                "inprop": "url",
            }

            try:
                r = requests.get(
                    _API_URL,
                    params=params,
                    headers={"User-Agent": _USER_AGENT},
                    timeout=30,
                )
                r.raise_for_status()
                data = r.json()
            except Exception:
                continue

            pages = list(((data.get("query") or {}).get("pages") or {}).values())
            if not pages:
                continue
            pages.sort(key=lambda p: int(p.get("index", 0)))

            for page_data in pages:
                infos = page_data.get("imageinfo") or []
                if not infos:
                    continue
                info = infos[0]
                download_url = info.get("url")
                if not download_url:
                    continue

                width = int(info.get("width") or 0)
                height = int(info.get("height") or 0)
                duration = float(info.get("duration") or 0.0)

                if kind == "video":
                    if min_duration is not None and duration and duration < min_duration:
                        continue
                    if max_duration is not None and duration and duration > max_duration:
                        continue

                score = round((width * height) / 1000000.0, 2)
                meta = info.get("extmetadata") or {}
                object_name = _meta_value(meta, "ObjectName")
                description = _meta_value(meta, "ImageDescription")
                categories = _meta_value(meta, "Categories")
                creator = _meta_value(meta, "Artist")
                tags = " ".join(part for part in (object_name, description, categories) if part).strip()[:500]

                title = page_data.get("title", "")
                page_id = str(page_data.get("pageid") or title.replace("File:", "", 1))
                page_url = info.get("descriptionurl") or page_data.get("canonicalurl") or ""

                item = MediaItem(
                    source_id=page_id,
                    kind=kind,
                    page_url=page_url,
                    download_url=download_url,
                    width=width,
                    height=height,
                    duration=duration,
                    creator=creator,
                    tags=tags,
                    score=score,
                )
                item.aspect_ratio = item.resolve_aspect_ratio()
                if aspect_ratio and item.aspect_ratio != aspect_ratio:
                    continue

                items.append(item)
                if len(items) >= per_page:
                    break

            if items:
                break

        items.sort(key=lambda x: x.score, reverse=True)
        return items[:per_page]

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        return self._search_media(
            query=query,
            kind="image",
            per_page=per_page,
            page=page,
            aspect_ratio=aspect_ratio,
        )

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        return self._search_media(
            query=query,
            kind="video",
            per_page=per_page,
            page=page,
            min_duration=min_duration,
            max_duration=max_duration,
            aspect_ratio=aspect_ratio,
        )

    def search(self, query: str, filters: SearchFilters) -> list[Candidate]:
        kind = (filters.kind or "any").lower()
        items: list[MediaItem] = []

        if kind in ("video", "any"):
            items.extend(
                self.search_videos(
                    query=query,
                    per_page=filters.per_page,
                    page=filters.page,
                    min_duration=filters.min_duration,
                    max_duration=filters.max_duration,
                    aspect_ratio=filters.orientation,
                )
            )
        if kind in ("image", "any") and len(items) < filters.per_page:
            items.extend(
                self.search_images(
                    query=query,
                    per_page=filters.per_page - len(items),
                    page=filters.page,
                    aspect_ratio=filters.orientation,
                )
            )

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
        parsed_path = urlparse(download_url).path
        suffix = Path(parsed_path).suffix or (".webm" if kind == "video" else ".jpg")
        target = out_dir / f"{kind}_{source_id}{suffix}"

        with requests.get(
            download_url,
            stream=True,
            timeout=300,
            headers={"User-Agent": _USER_AGENT},
        ) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return target


def search_wikimedia(inputs: dict[str, Any]) -> dict[str, Any]:
    query = inputs["query"]
    output_dir = Path(inputs.get("output_dir", "downloads")) / query.replace(" ", "_")
    video_count = max(0, int(inputs.get("video_count", 0)))
    image_count = max(0, int(inputs.get("image_count", 0)))
    if video_count == 0 and image_count == 0:
        video_count = 2

    aspect_ratio = inputs.get("aspect_ratio")
    min_duration = inputs.get("min_duration")
    max_duration = inputs.get("max_duration")
    max_workers = max(1, min(int(inputs.get("concurrent_downloads", 4)), 8))

    client = WikimediaSource()
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

        if image_count:
            images = client.search_images(
                query,
                per_page=image_count,
                aspect_ratio=aspect_ratio,
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
                    if path.exists() and item.kind == "image" and (item.width <= 0 or item.height <= 0):
                        try:
                            from PIL import Image
                            with Image.open(path) as img:
                                item.width, item.height = img.size
                                item.aspect_ratio = item.resolve_aspect_ratio()
                        except Exception:
                            pass

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
                        "quality_score": item.score,
                        "tags": item.tags,
                    })

        manifest_path = None
        if manifest_items:
            manifest_path = save_manifest(output_dir, query, "wikimedia", manifest_items)

        return {
            "success": bool(downloaded["videos"] or downloaded["images"]),
            "query": query,
            "provider": "wikimedia",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path) if manifest_path else "",
            "downloaded": downloaded,
            "items_count": len(manifest_items),
            "errors": errors,
        }
    except Exception as exc:
        return {"success": False, "error": f"Wikimedia search failed: {exc}"}
