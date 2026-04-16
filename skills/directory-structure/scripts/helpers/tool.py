"""
helpers/tool.py — Standalone shim for Agent Zero Tool & Response
================================================================
Provides drop-in replacements for the Agent Zero `Tool` base class
and `Response` dataclass so that existing tools can be used without
an Agent Zero runtime.

Drop this `helpers/` folder next to any Agent Zero tool script and
it will import cleanly. run_tool.py handles the rest.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# ── Response ──────────────────────────────────────────────────────────────────

@dataclass
class Response:
    """Mirrors the Agent Zero Response dataclass."""
    message: str
    break_loop: bool
    additional: Optional[dict[str, Any]] = None


# ── Tool ──────────────────────────────────────────────────────────────────────

class Tool:
    """
    Minimal standalone base class that mirrors the Agent Zero Tool interface.

    Only the attributes that tools actually USE are provided:
        self.args  — dict of arguments passed by the caller
        self.name  — tool name (defaults to class name)

    Everything Agent Zero-specific (agent, loop_data, log, PrintStyle, etc.)
    is silently absent; tools that reference those will raise AttributeError,
    which is the correct signal that they need further porting.
    """

    def __init__(self, args: Optional[dict] = None, name: str = "", **kwargs) -> None:
        self.args: dict[str, Any] = args or {}
        self.name: str = name or self.__class__.__name__

    async def execute(self, **kwargs) -> Response:
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute() must be implemented."
        )
