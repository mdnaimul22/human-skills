"""
helpers/tool.py — Standalone shim for Unified Tool & Response
================================================================
Provides drop-in replacements for the standard `Tool` base class
and `Response` dataclass so that existing tools can be used without
a specific framework runtime.

Drop this `helpers/` folder next to any tool script and
it will import cleanly. execute.py handles the rest.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# ── Response ──────────────────────────────────────────────────────────────────

@dataclass
class Response:
    """Mirrors the unified Response dataclass."""
    message: str
    break_loop: bool
    additional: Optional[dict[str, Any]] = None


# ── Tool ──────────────────────────────────────────────────────────────────────

class Tool:
    name: str = ""
    description: str = ""
    arguments: str = ""  # Document expected argument shape
    instruction: str = ""  # Where to read docs or how to use

    """
    Minimal standalone base class that mirrors the universal Tool interface.

    Only the attributes that tools actually USE are provided:
        self.args  — dict of arguments passed by the caller
        self.name  — tool name (defaults to class name)

    Everything framework-specific (agent, loop_data, log, PrintStyle, etc.)
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
