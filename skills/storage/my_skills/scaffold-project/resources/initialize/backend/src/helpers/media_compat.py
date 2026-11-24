from __future__ import annotations

NLE_COMPAT: dict[str, list[str]] = {
    "h264": ["Premiere Pro", "DaVinci Resolve", "Final Cut Pro", "CapCut", "Filmora"],
    "avc1": ["Premiere Pro", "DaVinci Resolve", "Final Cut Pro", "CapCut", "Filmora"],
    "h265": ["DaVinci Resolve", "Final Cut Pro"],
    "hevc": ["DaVinci Resolve", "Final Cut Pro"],
    "vp9": ["DaVinci Resolve"],
    "vp8": [],
    "av1": ["DaVinci Resolve 18+"],
    "aac": ["Premiere Pro", "DaVinci Resolve", "Final Cut Pro", "CapCut", "Filmora"],
    "opus": ["DaVinci Resolve"],
    "mp4a": ["Premiere Pro", "DaVinci Resolve", "Final Cut Pro", "CapCut", "Filmora"],
}

def get_nle_support(codec: str | None) -> list[str]:
    if not codec or codec == "none":
        return []
    base = codec.split(".")[0].lower()
    return NLE_COMPAT.get(base, [])
