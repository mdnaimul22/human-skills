from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
import requests


def search_pexels_video(inputs: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return {"success": False, "error": "PEXELS_API_KEY environment variable not set."}

    start = time.time()
    query = inputs["query"]
    params: dict[str, Any] = {
        "query": query,
        "per_page": inputs.get("per_page", 5),
        "page": inputs.get("page", 1),
    }
    if inputs.get("orientation"):
        params["orientation"] = inputs["orientation"]
    if inputs.get("size"):
        params["size"] = inputs["size"]

    try:
        search_response = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": api_key},
            params=params,
            timeout=30,
        )
        search_response.raise_for_status()
        data = search_response.json()

        videos = data.get("videos", [])
        min_dur = inputs.get("min_duration")
        max_dur = inputs.get("max_duration")
        if min_dur or max_dur:
            filtered = []
            for v in videos:
                dur = v.get("duration", 0)
                if min_dur and dur < min_dur:
                    continue
                if max_dur and dur > max_dur:
                    continue
                filtered.append(v)
            videos = filtered

        if not videos:
            return {
                "success": False,
                "error": f"No videos found for query: {query}",
                "data": {"total_results": data.get("total_results", 0)},
            }

        video = videos[0]
        preferred_quality = inputs.get("preferred_quality", "hd")
        video_files = video.get("video_files", [])
        selected_file = None
        for vf in sorted(video_files, key=lambda x: x.get("width", 0), reverse=True):
            if vf.get("quality") == preferred_quality:
                selected_file = vf
                break
        if not selected_file and video_files:
            selected_file = video_files[0]

        if not selected_file:
            return {"success": False, "error": "No downloadable video file found."}

        video_url = selected_file["link"]
        video_response = requests.get(video_url, timeout=120)
        video_response.raise_for_status()

        output_path = Path(inputs.get("output_path", f"pexels_video_{video['id']}.mp4"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(video_response.content)
    except Exception as exc:
        return {"success": False, "error": f"Pexels video search failed: {exc}"}

    return {
        "success": True,
        "data": {
            "provider": "pexels",
            "video_id": video["id"],
            "user": video.get("user", {}).get("name", "Unknown"),
            "duration_seconds": video.get("duration"),
            "width": selected_file.get("width"),
            "height": selected_file.get("height"),
            "fps": selected_file.get("fps"),
            "quality": selected_file.get("quality"),
            "query": query,
            "output": str(output_path),
            "total_results": data.get("total_results", 0),
            "results_returned": len(videos),
            "license": "Pexels License (free, no attribution required)",
            "pexels_url": video.get("url", ""),
        },
        "artifacts": [str(output_path)],
        "duration_seconds": round(time.time() - start, 2),
    }


class PexelsVideo:
    name = "pexels_video"

    def is_available(self) -> bool:
        return bool(os.environ.get("PEXELS_API_KEY"))

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return search_pexels_video(inputs)
