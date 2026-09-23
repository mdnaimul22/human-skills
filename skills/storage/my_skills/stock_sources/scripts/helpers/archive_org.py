from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
from typing import Any, Optional
from urllib.parse import urlparse
import requests

from .base import Candidate, MediaItem, SearchFilters, save_manifest

_SEARCH_URL = "https://archive.org/advancedsearch.php"
_METADATA_URL = "https://archive.org/metadata"
_DOWNLOAD_URL = "https://archive.org/download"

_DEFAULT_COLLECTIONS = ("prelinger", "opensource_movies", "home_movies")
_VIDEO_FORMAT_PRIORITY = (
    "h.264",
    "h.264 ia",
    "h.264 hd",
    "mpeg4",
    "512kb mpeg4",
    "matroska",
    "webm",
)
_MAX_FILE_SIZE_BYTES = 150 * 1024 * 1024
_DEFAULT_MAX_DURATION_SECONDS = 600.0
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

_STOP_WORDS = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "into",
    "its", "their", "about", "over", "under", "while", "during",
    "your", "you", "our", "are", "was", "were", "have", "has",
})

_SOURCE_HINT_TOKENS = frozenset({
    "prelinger", "archive", "archives", "stock", "footage",
})


def _looks_like_year(token: str) -> bool:
    bare = token.rstrip("s")
    return bare.isdigit() and len(bare) == 4


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


_HMS_RE = re.compile(r"^(\d+):(\d+):(\d+(?:\.\d+)?)$")
_MS_RE = re.compile(r"^(\d+):(\d+(?:\.\d+)?)$")


def _parse_length(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return 0.0
    m = _HMS_RE.match(s)
    if m:
        h, mn, sec = m.groups()
        return int(h) * 3600 + int(mn) * 60 + float(sec)
    m = _MS_RE.match(s)
    if m:
        mn, sec = m.groups()
        return int(mn) * 60 + float(sec)
    try:
        return float(s)
    except ValueError:
        return 0.0


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(x) for x in value if x is not None).strip()
    return str(value).strip()


def _pick_video_file(files: list[dict]) -> Optional[dict]:
    if not files:
        return None

    by_format: dict[str, list[dict]] = {}
    valid_extensions = (".mp4", ".m4v", ".mkv", ".webm", ".mov", ".avi")

    for f in files:
        fmt = (f.get("format") or "").strip().lower()
        name = (f.get("name") or "").lower()
        if any(tag in name for tag in ("thumb", "preview", ".gif", "subtitles")):
            continue
        if any(target in fmt for target in _VIDEO_FORMAT_PRIORITY) or any(name.endswith(ext) for ext in valid_extensions):
            key = fmt or "video"
            by_format.setdefault(key, []).append(f)

    for fmt in _VIDEO_FORMAT_PRIORITY:
        bucket = None
        for k in by_format:
            if fmt in k:
                bucket = by_format[k]
                break
        if not bucket:
            continue
        affordable = [
            f for f in bucket
            if 0 < _safe_int(f.get("size")) <= _MAX_FILE_SIZE_BYTES
        ]
        if not affordable:
            continue
        affordable.sort(
            key=lambda f: _safe_int(f.get("size")), reverse=True
        )
        return affordable[0]

    all_candidates: list[dict] = []
    for bucket in by_format.values():
        for f in bucket:
            if 0 < _safe_int(f.get("size")) <= _MAX_FILE_SIZE_BYTES:
                all_candidates.append(f)
    if all_candidates:
        all_candidates.sort(key=lambda f: _safe_int(f.get("size")), reverse=True)
        return all_candidates[0]

    return None


class ArchiveOrgSource:
    name = "archive_org"
    display_name = "Archive.org"
    provider = "archive_org"
    priority = 20
    supports = {"video": True, "image": False}

    def is_available(self) -> bool:
        return True

    def _build_queries(self, user_query: str) -> list[tuple[str, str]]:
        coll = " OR ".join(f"collection:{c}" for c in _DEFAULT_COLLECTIONS)
        user = user_query.strip()
        if not user:
            return [("default", f"mediatype:movies AND ({coll})")]

        tokens = [
            t for t in re.split(r"\s+", user)
            if len(t) >= 3
            and t.lower() not in _STOP_WORDS
            and t.lower() not in _SOURCE_HINT_TOKENS
        ]
        if not tokens:
            return [(
                "quoted_fallback",
                f'mediatype:movies AND ({coll}) AND ("{user}")',
            )]

        queries: list[tuple[str, str]] = []
        clean_phrase = " ".join(tokens)
        queries.append((
            "phrase_prox_10",
            f'mediatype:movies AND ({coll}) AND ("{clean_phrase}"~10)',
        ))

        non_year = [t for t in tokens if not _looks_like_year(t)]
        if len(non_year) >= 2:
            distinctive = sorted(non_year, key=lambda t: -len(t))[:2]
            and_q = " AND ".join(distinctive)
            queries.append((
                "distinctive_and",
                f"mediatype:movies AND ({coll}) AND ({and_q})",
            ))
        elif len(non_year) == 1:
            queries.append((
                "single_term",
                f"mediatype:movies AND ({coll}) AND ({non_year[0]})",
            ))

        top_tokens = sorted(tokens, key=lambda t: -len(t))[:3]
        or_q = " OR ".join(top_tokens)
        queries.append((
            "distinctive_or",
            f"mediatype:movies AND ({coll}) AND ({or_q})",
        ))

        return queries

    def _hydrate_media_item(
        self,
        doc: dict,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        aspect_ratio: Optional[str] = None,
    ) -> Optional[MediaItem]:
        identifier = doc.get("identifier")
        if not identifier:
            return None

        try:
            r = requests.get(f"{_METADATA_URL}/{identifier}/files", headers=_HEADERS, timeout=12)
            r.raise_for_status()
            data = r.json()
            files = data.get("result") or data.get("files") or []
        except Exception:
            return None

        picked = _pick_video_file(files)
        if picked is None:
            return None

        duration = _parse_length(picked.get("length"))
        effective_max = max_duration if max_duration is not None else _DEFAULT_MAX_DURATION_SECONDS

        if min_duration is not None and duration and duration < min_duration:
            return None
        if duration and duration > effective_max:
            return None

        width = _safe_int(picked.get("width"))
        height = _safe_int(picked.get("height"))
        file_name = picked.get("name", "")
        download_url = f"{_DOWNLOAD_URL}/{identifier}/{file_name}"

        title = _to_text(doc.get("title"))
        description = _to_text(doc.get("description"))
        subject = _to_text(doc.get("subject"))
        tags = " ".join(s for s in (title, description, subject) if s).strip()[:500]

        downloads = _safe_int(doc.get("downloads"))
        score = float(downloads)

        item = MediaItem(
            source_id=identifier,
            kind="video",
            page_url=f"https://archive.org/details/{identifier}",
            download_url=download_url,
            width=width,
            height=height,
            duration=duration,
            creator=_to_text(doc.get("creator")),
            tags=tags,
            downloads=downloads,
            score=score,
        )
        item.aspect_ratio = item.resolve_aspect_ratio()
        if aspect_ratio and item.aspect_ratio != aspect_ratio:
            return None

        return item

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        aspect_ratio: Optional[str] = None,
    ) -> list[MediaItem]:
        items: list[MediaItem] = []

        for _label, solr_q in self._build_queries(query):
            params = [
                ("q", solr_q),
                ("fl[]", "identifier"),
                ("fl[]", "title"),
                ("fl[]", "description"),
                ("fl[]", "creator"),
                ("fl[]", "date"),
                ("fl[]", "subject"),
                ("fl[]", "licenseurl"),
                ("fl[]", "collection"),
                ("fl[]", "downloads"),
                ("rows", str(max(1, min(per_page * 3, 50)))),
                ("page", str(max(1, page))),
                ("output", "json"),
            ]

            try:
                r = requests.get(_SEARCH_URL, headers=_HEADERS, params=params, timeout=20)
                r.raise_for_status()
                data = r.json()
            except Exception:
                continue

            docs = (data.get("response") or {}).get("docs", []) or []
            if not docs:
                continue

            for doc in docs:
                item = self._hydrate_media_item(
                    doc,
                    min_duration=min_duration,
                    max_duration=max_duration,
                    aspect_ratio=aspect_ratio,
                )
                if item is not None:
                    items.append(item)
                if len(items) >= per_page:
                    break

            if items:
                break

        items.sort(key=lambda x: x.score, reverse=True)
        return items[:per_page]

    def search(self, query: str, filters: SearchFilters) -> list[Candidate]:
        kind = (filters.kind or "video").lower()
        if kind not in ("video", "any"):
            return []

        media_items = self.search_videos(
            query=query,
            per_page=filters.per_page,
            page=filters.page,
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
                    thumbnail_url=f"https://archive.org/services/img/{it.source_id}",
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

        with requests.get(download_url, headers=_HEADERS, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return target


def search_archive_org(inputs: dict[str, Any]) -> dict[str, Any]:
    query = inputs["query"]
    output_dir = Path(inputs.get("output_dir", "downloads")) / query.replace(" ", "_")
    video_count = max(0, int(inputs.get("video_count", 3)))
    aspect_ratio = inputs.get("aspect_ratio")
    min_duration = inputs.get("min_duration")
    max_duration = inputs.get("max_duration")
    max_workers = max(1, min(int(inputs.get("concurrent_downloads", 4)), 8))

    client = ArchiveOrgSource()
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
                        "downloads": item.downloads,
                        "popularity_score": item.score,
                        "tags": item.tags,
                    })

        manifest_path = None
        if manifest_items:
            manifest_path = save_manifest(output_dir, query, "archive_org", manifest_items)

        return {
            "success": bool(downloaded["videos"]),
            "query": query,
            "provider": "archive_org",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path) if manifest_path else "",
            "downloaded": downloaded,
            "items_count": len(manifest_items),
            "errors": errors,
        }
    except Exception as exc:
        return {"success": False, "error": f"Archive.org search failed: {exc}"}
