from __future__ import annotations
import io
import tarfile
from unittest.mock import MagicMock, patch
import pytest
from src.apps.tunnel.helpers import TunnelInstaller, detect_platform
from src.config import Settings, delete, exists, is_file
from src.helpers import ExternalServiceError


def test_detect_platform_maps_linux_amd64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.platform.system", lambda: "Linux")
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.platform.machine", lambda: "x86_64")
    assert detect_platform() == ("linux", "amd64")
    assert TunnelInstaller.cloudflared_download_url().endswith("/cloudflared-linux-amd64")


def test_ensure_cloudflared_uses_system_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.shutil.which", lambda _b: "/usr/bin/cloudflared")
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.sys_is_file", lambda p: p == "/usr/bin/cloudflared")
    assert TunnelInstaller.ensure_cloudflared() == "/usr/bin/cloudflared"


def test_ensure_cloudflared_respects_auto_install_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.shutil.which", lambda _b: None)
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.is_file", lambda _p: False)
    monkeypatch.setattr(Settings, "TUNNEL_AUTO_INSTALL", False)
    with pytest.raises(ExternalServiceError, match="TUNNEL_AUTO_INSTALL=false"):
        TunnelInstaller.ensure_cloudflared()


def test_ensure_cloudflared_downloads_into_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    test_bin_dir = "data/apps/tunnel/test_bin_cf"
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.BIN_DIR_REL", test_bin_dir)
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.shutil.which", lambda _b: None)
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.platform.system", lambda: "Linux")
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.platform.machine", lambda: "x86_64")
    monkeypatch.setattr(Settings, "TUNNEL_AUTO_INSTALL", True)

    mock_resp = MagicMock()
    mock_resp.read.return_value = b"#!/bin/sh\necho ok\n"
    mock_resp.__enter__.return_value = mock_resp

    try:
        with patch("src.apps.tunnel.helpers.installer.urllib.request.urlopen", return_value=mock_resp):
            resolved = TunnelInstaller.ensure_cloudflared()
        assert resolved.endswith(f"{test_bin_dir}/cloudflared")
        assert is_file(f"{test_bin_dir}/cloudflared")
    finally:
        if exists(test_bin_dir):
            delete(test_bin_dir)


def test_ensure_tailscale_extracts_tar_binaries(monkeypatch: pytest.MonkeyPatch) -> None:
    test_bin_dir = "data/apps/tunnel/test_bin_ts"
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.BIN_DIR_REL", test_bin_dir)
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.shutil.which", lambda _b: None)
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.platform.system", lambda: "Linux")
    monkeypatch.setattr("src.apps.tunnel.helpers.installer.platform.machine", lambda: "x86_64")
    monkeypatch.setattr(Settings, "TUNNEL_AUTO_INSTALL", True)
    monkeypatch.setattr(
        TunnelInstaller,
        "tailscale_archive_url",
        classmethod(lambda _cls: "https://pkgs.tailscale.com/stable/tailscale_1.80.0_amd64.tgz"),
    )

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in (("tailscale_1.80.0_amd64/tailscale", b"ts-cli"), ("tailscale_1.80.0_amd64/tailscaled", b"ts-daemon")):
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    tar_bytes = buf.getvalue()

    mock_resp = MagicMock()
    mock_resp.read.return_value = tar_bytes
    mock_resp.__enter__.return_value = mock_resp

    try:
        with patch("src.apps.tunnel.helpers.installer.urllib.request.urlopen", return_value=mock_resp):
            cli_bin, daemon_bin = TunnelInstaller.ensure_tailscale()
        assert cli_bin.endswith(f"{test_bin_dir}/tailscale")
        assert daemon_bin is not None and daemon_bin.endswith(f"{test_bin_dir}/tailscaled")
        assert is_file(f"{test_bin_dir}/tailscale")
        assert is_file(f"{test_bin_dir}/tailscaled")
    finally:
        if exists(test_bin_dir):
            delete(test_bin_dir)
