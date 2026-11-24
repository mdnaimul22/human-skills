from __future__ import annotations
import os
import platform
import re
import shutil
import tarfile
import urllib.parse
import urllib.request
from typing import Callable, Optional
from src.config import Settings, delete, ensure_dir, get_abs_path, is_file, setup_logger, sys_is_file, write_bytes
from src.helpers import ExternalServiceError
from ..schema import TunnelEventType

logger = setup_logger(Settings.LOG_DIR / "tunnel.log", name="apps.tunnel.installer")

NotifyCallback = Callable[[TunnelEventType, str, Optional[str]], None]

BIN_DIR_REL = "data/apps/tunnel/bin"
_CLOUDFLARED_BASE_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download"
_TAILSCALE_PACKAGES_URL = "https://pkgs.tailscale.com/stable/?v=latest"


def detect_platform() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch_map = {
        "x86_64": "amd64", "amd64": "amd64",
        "aarch64": "arm64", "arm64": "arm64",
        "i386": "386", "i686": "386", "x86": "386",
    }
    arch = arch_map.get(machine, "arm" if machine.startswith("arm") else "")
    if not arch:
        raise ExternalServiceError("TunnelInstaller", f"Unsupported CPU architecture: {machine}")
    if system not in {"linux", "darwin", "windows"}:
        raise ExternalServiceError("TunnelInstaller", f"Unsupported operating system: {system}")
    return system, arch


def executable_name(name: str, system_name: Optional[str] = None) -> str:
    sys_name = (system_name or platform.system()).lower()
    return f"{name}.exe" if sys_name == "windows" else name


def _chmod_exec(abs_path: str) -> None:
    if platform.system().lower() != "windows":
        os.chmod(abs_path, 0o755)


def _emit(notify: Optional[NotifyCallback], event: TunnelEventType, message: str) -> None:
    if notify is not None:
        notify(event, message, None)


def _download_atomic(url: str, dest_rel: str, notify: Optional[NotifyCallback] = None) -> str:
    ensure_dir(dest_rel.rsplit("/", 1)[0])
    tmp_rel = f"{dest_rel}.download"
    _emit(notify, TunnelEventType.DOWNLOADING, f"Downloading {url}")
    logger.info(f"tunnel.installer.download url={url} dest={dest_rel}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ScaffoldTunnelInstaller/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = resp.read()
        write_bytes(tmp_rel, payload)
        abs_tmp = get_abs_path(tmp_rel)
        abs_dest = get_abs_path(dest_rel)
        os.replace(abs_tmp, abs_dest)
        _emit(notify, TunnelEventType.DOWNLOAD_COMPLETE, f"Downloaded {dest_rel.rsplit('/', 1)[-1]}")
        return abs_dest
    except Exception as err:
        if is_file(tmp_rel):
            delete(tmp_rel)
        raise ExternalServiceError("TunnelInstaller", f"Download failed for '{url}': {err}") from err


def _extract_tar_binaries(archive_rel: str, dest_dir_rel: str, names: set[str]) -> dict[str, str]:
    ensure_dir(dest_dir_rel)
    extracted: dict[str, str] = {}
    abs_archive = get_abs_path(archive_rel)
    with tarfile.open(abs_archive, "r:*") as archive:
        for member in archive.getmembers():
            base_name = member.name.rsplit("/", 1)[-1]
            if base_name not in names or not member.isfile():
                continue
            stream = archive.extractfile(member)
            if stream is None:
                continue
            target_rel = f"{dest_dir_rel}/{executable_name(base_name)}"
            with stream:
                write_bytes(target_rel, stream.read())
            abs_target = get_abs_path(target_rel)
            _chmod_exec(abs_target)
            extracted[base_name] = abs_target
    missing = names - set(extracted.keys())
    if missing:
        raise ExternalServiceError("TunnelInstaller", f"Archive missing expected binaries: {', '.join(sorted(missing))}")
    return extracted


class TunnelInstaller:
    @classmethod
    def cloudflared_download_url(cls) -> str:
        system, arch = detect_platform()
        if system == "linux":
            return f"{_CLOUDFLARED_BASE_URL}/cloudflared-linux-{arch}"
        if system == "windows":
            return f"{_CLOUDFLARED_BASE_URL}/cloudflared-windows-{arch}.exe"
        return f"{_CLOUDFLARED_BASE_URL}/cloudflared-darwin-{arch}.tgz"

    @classmethod
    def ensure_cloudflared(cls, notify: Optional[NotifyCallback] = None) -> str:
        existing = shutil.which("cloudflared")
        if existing and sys_is_file(existing):
            return existing
        bin_rel = f"{BIN_DIR_REL}/{executable_name('cloudflared')}"
        if is_file(bin_rel):
            return get_abs_path(bin_rel)
        if not Settings.TUNNEL_AUTO_INSTALL:
            raise ExternalServiceError("Cloudflared", "cloudflared binary not found and TUNNEL_AUTO_INSTALL=false")
        url = cls.cloudflared_download_url()
        if url.endswith(".tgz"):
            archive_rel = f"{BIN_DIR_REL}/cloudflared.tgz"
            _download_atomic(url, archive_rel, notify=notify)
            try:
                extracted = _extract_tar_binaries(archive_rel, BIN_DIR_REL, {"cloudflared"})
                return extracted["cloudflared"]
            finally:
                if is_file(archive_rel):
                    delete(archive_rel)
        abs_bin = _download_atomic(url, bin_rel, notify=notify)
        _chmod_exec(abs_bin)
        return abs_bin

    @classmethod
    def resolve_tailscaled(cls, tailscale_bin: str) -> Optional[str]:
        parent = tailscale_bin.rsplit("/", 1)[0] if "/" in tailscale_bin else ""
        if parent:
            sibling = f"{parent}/{executable_name('tailscaled')}"
            if sys_is_file(sibling):
                return sibling
        found = shutil.which("tailscaled")
        if found and sys_is_file(found):
            return found
        managed_rel = f"{BIN_DIR_REL}/{executable_name('tailscaled')}"
        return get_abs_path(managed_rel) if is_file(managed_rel) else None

    @classmethod
    def tailscale_archive_url(cls) -> str:
        _, arch = detect_platform()
        req = urllib.request.Request(_TAILSCALE_PACKAGES_URL, headers={"User-Agent": "ScaffoldTunnelInstaller/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as err:
            raise ExternalServiceError("Tailscale", f"Failed querying Tailscale package index: {err}") from err
        match = re.search(rf'href="([^"]*tailscale_[^"]+_{re.escape(arch)}\.tgz)"', html)
        if not match:
            raise ExternalServiceError("Tailscale", f"No Tailscale static package found for arch '{arch}'")
        return urllib.parse.urljoin(_TAILSCALE_PACKAGES_URL, match.group(1))

    @classmethod
    def ensure_tailscale(cls, notify: Optional[NotifyCallback] = None) -> tuple[str, Optional[str]]:
        existing = shutil.which("tailscale")
        if existing and sys_is_file(existing):
            return existing, cls.resolve_tailscaled(existing)
        cli_rel = f"{BIN_DIR_REL}/{executable_name('tailscale')}"
        daemon_rel = f"{BIN_DIR_REL}/{executable_name('tailscaled')}"
        if is_file(cli_rel) and is_file(daemon_rel):
            return get_abs_path(cli_rel), get_abs_path(daemon_rel)
        if not Settings.TUNNEL_AUTO_INSTALL:
            raise ExternalServiceError("Tailscale", "tailscale binary not found and TUNNEL_AUTO_INSTALL=false")
        url = cls.tailscale_archive_url()
        archive_name = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1] or "tailscale.tgz"
        archive_rel = f"{BIN_DIR_REL}/{archive_name}"
        _download_atomic(url, archive_rel, notify=notify)
        try:
            extracted = _extract_tar_binaries(archive_rel, BIN_DIR_REL, {"tailscale", "tailscaled"})
            return extracted["tailscale"], extracted["tailscaled"]
        finally:
            if is_file(archive_rel):
                delete(archive_rel)
