"""
Date & Time Utilities
======================
Standardized ISO 8601 timestamps (UTC) and human-readable relative time.
Zero external dependencies — uses only Python stdlib.

Usage:
    from src.helpers.date_utils import time_now_iso, format_iso, relative_time
"""

from datetime import datetime, timezone


def time_now() -> datetime:
    """Get current UTC datetime object."""
    return datetime.now(timezone.utc)


def time_now_iso() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def format_iso(dt: datetime) -> str:
    """Format a datetime object to ISO 8601 string (UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def parse_iso(iso_str: str) -> datetime:
    """Parse an ISO 8601 string into a timezone-aware datetime."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def relative_time(dt: datetime) -> str:
    """
    Human-readable relative time string.

    Examples:
        "just now", "2 minutes ago", "3 hours ago", "5 days ago"
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = now - dt

    seconds = int(delta.total_seconds())

    if seconds < 0:
        return "in the future"
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if seconds < 2592000:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    if seconds < 31536000:
        months = seconds // 2592000
        return f"{months} month{'s' if months != 1 else ''} ago"

    years = seconds // 31536000
    return f"{years} year{'s' if years != 1 else ''} ago"
