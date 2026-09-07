"""
Low-level Tailscale subprocess wrapper. No business logic — pure CLI execution.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Optional

from src.config import Settings, setup_logger

logger = setup_logger(Settings.LOG_DIR / "provider.log", name="app.providers.tailscale")


def is_tailscale_installed() -> bool:
    """Check if the tailscale CLI executable is available in PATH."""
    return shutil.which("tailscale") is not None


def run_tailscale_json(args: list[str], timeout: int = 5) -> tuple[bool, Optional[dict[str, Any]], str]:
    """Execute a tailscale JSON command and return (success, parsed_json, error_message)."""
    if not is_tailscale_installed():
        return False, None, "tailscale CLI is not installed"

    cmd = ["tailscale"] + args + ["--json"]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if r.returncode != 0:
            err = r.stderr.strip() or r.stdout.strip()
            return False, None, err

        stdout = r.stdout.strip()
        if not stdout:
            return True, {}, ""
        data = json.loads(stdout)
        return True, data, ""
    except subprocess.TimeoutExpired:
        msg = f"tailscale command timed out after {timeout}s"
        logger.warning(msg)
        return False, None, msg
    except json.JSONDecodeError as exc:
        msg = f"Failed to parse tailscale output as JSON: {exc}"
        logger.warning(msg)
        return False, None, msg
    except Exception as exc:
        msg = f"Failed to execute tailscale: {exc}"
        logger.error(f"Tailscale execution error: {exc}")
        return False, None, msg


def run_tailscale_cmd(args: list[str], timeout: int = 10) -> tuple[bool, str]:
    """Execute a tailscale command and return (success, message)."""
    if not is_tailscale_installed():
        return False, "tailscale CLI is not installed"

    cmd = ["tailscale"] + args
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode == 0:
            return True, out or "Success"
        return False, err or out or f"tailscale exited with code {r.returncode}"
    except subprocess.TimeoutExpired:
        return False, f"tailscale command timed out after {timeout}s"
    except Exception as exc:
        logger.error(f"Tailscale command error: {exc}")
        return False, str(exc)