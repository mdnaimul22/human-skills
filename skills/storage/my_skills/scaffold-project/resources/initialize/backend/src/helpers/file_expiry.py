from __future__ import annotations

from datetime import timedelta
from src.config import Settings

def _build_ttl_map() -> dict[str, timedelta]:
    return {
        "guest": timedelta(seconds=Settings.GUEST_FILE_TTL),
        "registered": timedelta(seconds=Settings.REGISTERED_FILE_TTL),
        "premium": timedelta(seconds=Settings.PREMIUM_FILE_TTL),
    }

def resolve_ttl(user_id: str | None = None, user_tier: str | None = None) -> tuple[str, timedelta]:
    ttl_map = _build_ttl_map()
    if not user_id:
        return "guest", ttl_map["guest"]
    tier = user_tier if user_tier in ttl_map else "registered"
    return tier, ttl_map[tier]
