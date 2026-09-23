from __future__ import annotations

import time
from typing import Any

try:
    from ._shared import HUNYUAN_VARIANTS, generate_local_video
except ImportError:
    from tools.video._shared import HUNYUAN_VARIANTS, generate_local_video


def generate_hunyuan_video(inputs: dict[str, Any]) -> Any:
    start = time.time()
    try:
        result = generate_local_video(
            tool_name="hunyuan_video",
            variants=HUNYUAN_VARIANTS,
            default_variant="hunyuan-1.5",
            inputs=inputs,
        )
        if hasattr(result, "duration_seconds"):
            result.duration_seconds = round(time.time() - start, 2)
        return result
    except Exception as exc:
        return {"success": False, "error": f"Hunyuan video generation failed: {exc}"}


class HunyuanVideo:
    name = "hunyuan_video"

    def execute(self, inputs: dict[str, Any]) -> Any:
        return generate_hunyuan_video(inputs)
