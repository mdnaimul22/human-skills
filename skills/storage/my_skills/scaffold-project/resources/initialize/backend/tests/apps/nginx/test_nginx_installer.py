from __future__ import annotations

from unittest.mock import MagicMock, patch
from src.apps.nginx.helpers.installer import Installer


def test_is_installed_true() -> None:
    with patch("shutil.which", return_value="/usr/sbin/nginx"):
        assert Installer.is_installed() is True


def test_is_installed_false() -> None:
    with patch("shutil.which", return_value=None):
        assert Installer.is_installed() is False


def test_ensure_installed_already_present() -> None:
    with patch.object(Installer, "is_installed", return_value=True):
        assert Installer.ensure_installed() is True


def test_ensure_installed_no_apt_get() -> None:
    with patch.object(Installer, "is_installed", return_value=False):
        with patch("shutil.which", return_value=None):
            assert Installer.ensure_installed() is False


def test_ensure_installed_success() -> None:
    mock_run = MagicMock(returncode=0)
    with patch("shutil.which", side_effect=[None, "/usr/bin/apt-get", "/usr/sbin/nginx"]):
        with patch("subprocess.run", return_value=mock_run):
            assert Installer.ensure_installed() is True


def test_ensure_installed_failure_returncode() -> None:
    mock_run = MagicMock(returncode=1, stderr="lock error")
    with patch.object(Installer, "is_installed", side_effect=[False, False]):
        with patch("shutil.which", return_value="/usr/bin/apt-get"):
            with patch("subprocess.run", return_value=mock_run):
                assert Installer.ensure_installed() is False


def test_ensure_installed_catches_exception() -> None:
    with patch.object(Installer, "is_installed", return_value=False):
        with patch("shutil.which", return_value="/usr/bin/apt-get"):
            with patch("subprocess.run", side_effect=RuntimeError("exec error")):
                assert Installer.ensure_installed() is False


def test_ensure_dirs_success() -> None:
    mock_res = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_res) as mock_cmd, patch(
        "src.apps.nginx.helpers.installer.sys_exists", return_value=True
    ):
        assert Installer.ensure_dirs() is True
        assert mock_cmd.call_count >= 1


def test_ensure_dirs_exception() -> None:
    with patch("src.apps.nginx.helpers.installer.subprocess.run", side_effect=RuntimeError("disk full")):
        assert Installer.ensure_dirs() is False
