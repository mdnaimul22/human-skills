from __future__ import annotations
from .auth import router as auth_router
from .system import router as system_router

__all__ = ["auth_router", "system_router"]
