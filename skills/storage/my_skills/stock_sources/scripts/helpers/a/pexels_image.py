from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
import requests


def search_pexels_image(inputs: dict[str, Any]) -> dict[str, Any]:
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
    if inputs.get("color"):
        params["color"] = inputs["color"]

    try:
        search_response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params=params,
            timeout=30,
        )
        search_response.raise_for_status()
        data = search_response.json()

        photos = data.get("photos", [])
        if not photos:
            return {
                "success": False,
                "error": f"No images found for query: {query}",
                "data": {"total_results": data.get("total_results", 0)},
            }

        photo = photos[0]
        download_size = inputs.get("download_size", "large2x")
        image_url = photo["src"].get(download_size, photo["src"]["large2x"])

        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()

        output_path = Path(inputs.get("output_path", f"pexels_{photo['id']}.jpg"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_response.content)
    except Exception as exc:
        return {"success": False, "error": f"Pexels image search failed: {exc}"}

    return {
        "success": True,
        "data": {
            "provider": "pexels",
            "photo_id": photo["id"],
            "photographer": photo.get("photographer", "Unknown"),
            "photographer_url": photo.get("photographer_url", ""),
            "alt": photo.get("alt", ""),
            "width": photo.get("width"),
            "height": photo.get("height"),
            "query": query,
            "output": str(output_path),
            "total_results": data.get("total_results", 0),
            "results_returned": len(photos),
            "license": "Pexels License (free, no attribution required)",
            "pexels_url": photo.get("url", ""),
        },
        "artifacts": [str(output_path)],
        "duration_seconds": round(time.time() - start, 2),
    }


class PexelsImage:
    name = "pexels_image"

    def is_available(self) -> bool:
        return bool(os.environ.get("PEXELS_API_KEY"))

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return search_pexels_image(inputs)
