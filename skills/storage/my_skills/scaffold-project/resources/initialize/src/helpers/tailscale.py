from __future__ import annotations

import asyncio
import json
import shutil
from typing import Optional

from src.config import Settings, setup_logger
from src.helpers.exceptions import ExternalServiceError

logger = setup_logger(boss_name="helpers.main.txt", his_name="helpers.tailscale.txt")


def is_tailscale_installed() -> bool:
    return shutil.which("tailscale") is not None


def get_tailscale_guidance(kind: str = "install", auth_url: Optional[str] = None) -> str:
    target = kind.lower().replace("_guidance", "").strip()
    if target == "install":
        return (
            "\n======================================================================\n"
            "🚨 [Tailscale Missing] Tailscale CLI is not installed on this system.\n"
            "👉 To install Tailscale, run in terminal:\n"
            "   curl -fsSL https://tailscale.com/install.sh | sh\n"
            "📖 Official documentation: https://tailscale.com/download\n"
            "======================================================================\n"
        )
    if target == "login":
        url_msg = f"\n   Login URL: {auth_url}" if auth_url else ""
        return (
            "\n======================================================================\n"
            "⚠️ [Tailscale Auth Required] Device is not authenticated to your Tailnet.\n"
            "👉 Authenticate this device by running:\n"
            f"   tailscale login{url_msg}\n"
            "======================================================================\n"
        )
    if target == "daemon":
        return (
            "\n======================================================================\n"
            "🚨 [Tailscale Daemon Stopped] tailscaled daemon is not running.\n"
            "👉 Start the daemon by running:\n"
            "   sudo systemctl start tailscaled\n"
            "======================================================================\n"
        )
    if target == "stopped":
        return (
            "\n======================================================================\n"
            "🚨 [Tailscale Stopped] Tailscale connection is stopped.\n"
            "👉 Connect to Tailnet by running in terminal:\n"
            "   tailscale up\n"
            "======================================================================\n"
        )
    return ""


async def run_tailscale_cmd(args: list[str], timeout: float = 10.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "tailscale",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", f"Command 'tailscale {' '.join(args)}' timed out after {timeout}s"


async def get_tailscale_status() -> dict:
    rc, stdout, stderr = await run_tailscale_cmd(["status", "--json"])
    if rc != 0 or not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        logger.warning(f"Failed to parse tailscale status JSON: {exc}")
        return {}


def _is_port_in_funnel(funnel_data: dict, port: int) -> bool:
    target = f":{port}"
    web_map = funnel_data.get("Web", {})
    for node in web_map.values():
        handlers = node.get("Handlers", {})
        for h in handlers.values():
            if target in str(h.get("Proxy", "")):
                return True
    return False


async def ensure_tailscale_funnel(port: Optional[int] = None) -> bool:
    target_port = port if port is not None else Settings.API_PORT
    rc, stdout, _ = await run_tailscale_cmd(["funnel", "status", "--json"])
    if rc == 0 and stdout:
        try:
            funnel_data = json.loads(stdout)
            if _is_port_in_funnel(funnel_data, target_port):
                return True
        except json.JSONDecodeError as exc:
            logger.warning(f"Failed to parse funnel status JSON: {exc}")

    frc, fout, ferr = await run_tailscale_cmd(["funnel", "--bg", str(target_port)])
    if frc != 0:
        logger.error(f"Failed to enable Tailscale Funnel: {ferr or fout}")
        return False
    return True


async def reset_tailscale_serve() -> bool:
    rc, _, stderr = await run_tailscale_cmd(["serve", "reset"])
    if rc != 0:
        logger.warning(f"Tailscale serve reset warning: {stderr}")
        return False
    return True


async def setup_tailscale_ingress(port: Optional[int] = None) -> str:
    target_port = port if port is not None else Settings.API_PORT
    if not is_tailscale_installed():
        guidance = get_tailscale_guidance("install")
        logger.error(guidance)
        raise ExternalServiceError("Tailscale", "Tailscale CLI is not installed on this system")

    status = await get_tailscale_status()
    if not status:
        guidance = get_tailscale_guidance("daemon")
        logger.error(guidance)
        raise ExternalServiceError("Tailscale", "Tailscale daemon (tailscaled) is not running")

    backend_state = status.get("BackendState", "")
    if backend_state == "NeedsLogin":
        auth_url = status.get("AuthURL")
        guidance = get_tailscale_guidance("login", auth_url=auth_url)
        logger.error(guidance)
        raise ExternalServiceError("Tailscale", "Tailscale authentication required")


    if backend_state == "Stopped":
        guidance = get_tailscale_guidance("stopped")
        logger.error(guidance)
        raise ExternalServiceError("Tailscale", "Tailscale connection is stopped. Run 'tailscale up'")

    if backend_state != "Running":
        logger.error(f"Tailscale backend state invalid: '{backend_state}'")
        raise ExternalServiceError("Tailscale", f"Tailscale state '{backend_state}' is not running")


    self_node = status.get("Self", {})
    raw_dns = self_node.get("DNSName", "")
    dns_name = raw_dns.rstrip(".")
    if not dns_name:
        raise ExternalServiceError("Tailscale", "Unable to determine Tailscale node DNS name")

    funnel_ok = await ensure_tailscale_funnel(target_port)
    if not funnel_ok:
        raise ExternalServiceError("Tailscale", f"Failed to activate Tailscale Funnel on port {target_port}")

    public_url = f"https://{dns_name}"
    Settings.PUBLIC_URL = public_url

    logger.info(
        f"\n======================================================================\n"
        f"🌐 [Tailscale Ingress Active]\n"
        f"🚀 Server successfully exposed to the internet!\n"
        f"🔗 Public URL: {public_url}\n"
        f"======================================================================\n"
    )
    return public_url
