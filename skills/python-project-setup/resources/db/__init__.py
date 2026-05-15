"""
Database Layer — Exports
=========================
Single import point for the DB layer.

Usage:
    from src.db import init_db, get_session, shutdown_db, BaseRepository
"""

from .connection import init_db, get_session, shutdown_db
from .repository import BaseRepository

__all__ = [
    "init_db",
    "get_session",
    "shutdown_db",
    "BaseRepository",
]
