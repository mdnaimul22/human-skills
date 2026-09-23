from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Optional

try:
    from helpers.tool import Tool, Response
except ImportError:
    from skills.helpers.tool import Tool, Response

try:
    from skills.storage.my_skills.stock_sources.scripts.helpers.pixabay import search_pixabay
    from skills.storage.my_skills.stock_sources.scripts.helpers.pexels import search_pexels
    from skills.storage.my_skills.stock_sources.scripts.helpers.archive_org import search_archive_org
    from skills.storage.my_skills.stock_sources.scripts.helpers.base import save_manifest
except ImportError:
    import importlib.util
    _h_dir = Path(__file__).resolve().parent / "helpers"

    def _load_helper(name: str):
        spec = importlib.util.spec_from_file_location(f"stock_helper_{name}", _h_dir / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    _pix = _load_helper("pixabay")
    _pex = _load_helper("pexels")
    _arc = _load_helper("archive_org")
    _bas = _load_helper("base")
    search_pixabay = _pix.search_pixabay
    search_pexels = _pex.search_pexels
    search_archive_org = _arc.search_archive_org
    save_manifest = _bas.save_manifest

_VALID_SOURCES = ("pixabay", "pexels", "archive_org")


class StockCollector(Tool):
    name: str = "stock_collector"
    description: str = "Unified stock media downloader across Pixabay, Pexels, and Archive.org with popularity ranking, aspect ratio, duration filtering, color palette extraction, and manifest generation."
    arguments: dict = {
        "query": "Search term or prompt (REQUIRED).",
        "sources": "Stock providers to search: 'all' (default), 'pixabay', 'pexels', 'archive_org', or comma-separated.",
        "video_count": "Number of videos to download per provider (default: 2).",
        "image_count": "Number of images to download per provider (default: 2).",
        "aspect_ratio": "Filter by aspect ratio: 'horizontal', 'vertical', 'square' (optional).",
        "min_duration": "Minimum video duration in seconds (optional).",
        "max_duration": "Maximum video duration in seconds (optional).",
        "color": "Color filter for Pexels or Pixabay (e.g. 'orange', 'blue', 'black', 'white').",
        "output_dir": "Target base directory where media files and manifest.json will be saved (default: 'downloads').",
        "concurrent_downloads": "Number of parallel download threads (default: 6)."
    }
    instruction: str = "For detailed skill instructions run: human-skills --skill_info stock_sources"

    async def execute(self, **kwargs) -> Response:
        query = self.args.get("query")
        if not query or not str(query).strip():
            return Response(message="❌ Error: 'query' argument is required.", break_loop=False)

        query = str(query).strip()
        sources_arg = str(self.args.get("sources", "all")).lower().strip()
        video_count = max(0, int(self.args.get("video_count", 2)))
        image_count = max(0, int(self.args.get("image_count", 2)))
        aspect_ratio = self.args.get("aspect_ratio")
        min_duration = self.args.get("min_duration")
        max_duration = self.args.get("max_duration")
        color = self.args.get("color")
        base_output_dir = Path(self.args.get("output_dir", "downloads"))
        target_dir = base_output_dir / query.replace(" ", "_")
        concurrent_downloads = max(1, min(int(self.args.get("concurrent_downloads", 6)), 12))

        enabled_sources: list[str] = []
        if sources_arg in ("all", "*"):
            enabled_sources = list(_VALID_SOURCES)
        else:
            for s in sources_arg.split(","):
                s = s.strip()
                if s in _VALID_SOURCES and s not in enabled_sources:
                    enabled_sources.append(s)

        if not enabled_sources:
            return Response(
                message=f"❌ Error: Invalid sources '{sources_arg}'. Supported: {', '.join(_VALID_SOURCES)}, or 'all'.",
                break_loop=False,
            )

        results: dict[str, Any] = {}
        all_manifest_items: list[dict[str, Any]] = []
        all_downloaded_videos: list[str] = []
        all_downloaded_images: list[str] = []
        errors: list[str] = []

        for source in enabled_sources:
            params = {
                "query": query,
                "output_dir": str(base_output_dir),
                "video_count": video_count,
                "image_count": image_count,
                "aspect_ratio": aspect_ratio,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "concurrent_downloads": concurrent_downloads,
            }
            if color:
                if source == "pixabay":
                    params["colors"] = color
                else:
                    params["color"] = color

            if source == "pixabay":
                res = search_pixabay(params)
            elif source == "pexels":
                res = search_pexels(params)
            elif source == "archive_org":
                res = search_archive_org(params)
            else:
                continue

            results[source] = res
            if not res.get("success") and res.get("error"):
                errors.append(f"{source}: {res['error']}")
                continue

            dl = res.get("downloaded", {})
            all_downloaded_videos.extend(dl.get("videos", []))
            all_downloaded_images.extend(dl.get("images", []))

            manifest_p = res.get("manifest_path")
            if manifest_p and Path(manifest_p).exists():
                try:
                    with open(manifest_p, "r", encoding="utf-8") as mf:
                        m_data = json.load(mf)
                        for it in m_data.get("items", []):
                            it["provider"] = source
                            all_manifest_items.append(it)
                except Exception as exc:
                    errors.append(f"Failed to read {source} manifest: {exc}")

        total_downloaded = len(all_downloaded_videos) + len(all_downloaded_images)
        if total_downloaded == 0:
            err_msg = "\n".join(errors) if errors else "No media found matching criteria."
            return Response(message=f"❌ Download failed for query '{query}':\n{err_msg}", break_loop=False)

        master_manifest_path = target_dir / "manifest.json"
        target_dir.mkdir(parents=True, exist_ok=True)
        master_manifest_data = {
            "query": query,
            "providers": enabled_sources,
            "total_items": len(all_manifest_items),
            "total_videos": len(all_downloaded_videos),
            "total_images": len(all_downloaded_images),
            "items": all_manifest_items,
        }
        master_manifest_path.write_text(
            json.dumps(master_manifest_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        msg_lines = [
            f"✅ Stock media collected successfully for: '{query}'",
            f"📁 Target Directory: {target_dir}",
            f"📄 Master Manifest: {master_manifest_path}",
            f"📊 Total Downloaded: {total_downloaded} items ({len(all_downloaded_videos)} videos, {len(all_downloaded_images)} images)",
            "",
            "📋 Download Details:",
        ]

        for it in all_manifest_items:
            prov = it.get("provider", "unknown").upper()
            k = it.get("kind", "media").upper()
            res_str = it.get("resolution", "N/A")
            ratio = it.get("aspect_ratio", "N/A")
            dur = f"{it['duration_seconds']}s" if it.get("duration_seconds") else "N/A"
            size = f"{it.get('file_size_mb', 0)} MB"
            extra_info = []
            if it.get("avg_color"):
                extra_info.append(f"color={it['avg_color']}")
            if it.get("views"):
                extra_info.append(f"views={it['views']:,}")
            if it.get("downloads"):
                extra_info.append(f"downloads={it['downloads']:,}")
            if it.get("likes"):
                extra_info.append(f"likes={it['likes']:,}")
            if it.get("popularity_score"):
                extra_info.append(f"popularity={it['popularity_score']}")
            elif it.get("quality_score"):
                extra_info.append(f"quality={it['quality_score']}")

            details_suffix = f" [{', '.join(extra_info)}]" if extra_info else ""
            msg_lines.append(
                f"  • [{prov}] [{k}] {it.get('file_name')} ({res_str}, {ratio}, {dur}, {size}){details_suffix}"
            )

        if errors:
            msg_lines.append("")
            msg_lines.append("⚠️ Warnings:")
            for err in errors:
                msg_lines.append(f"  • {err}")

        return Response(message="\n".join(msg_lines), break_loop=False)
