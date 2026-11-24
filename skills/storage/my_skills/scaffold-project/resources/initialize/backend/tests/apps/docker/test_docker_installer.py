from __future__ import annotations
import subprocess
from unittest.mock import MagicMock, patch
from src.apps.docker.helpers.installer import Installer

def test_is_installed() -> None:
    with patch("shutil.which", return_value="/usr/bin/docker"):
        assert Installer.is_installed() is True
    with patch("shutil.which", return_value=None):
        assert Installer.is_installed() is False

def test_is_daemon_running_when_cli_missing() -> None:
    with patch("shutil.which", return_value=None):
        assert Installer.is_daemon_running() is False

def test_is_daemon_running_when_active() -> None:
    mock_res = MagicMock(returncode=0)
    with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run", return_value=mock_res):
        assert Installer.is_daemon_running() is True

def test_is_daemon_running_when_inactive() -> None:
    mock_res = MagicMock(returncode=1)
    with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run", return_value=mock_res):
        assert Installer.is_daemon_running() is False

def test_is_daemon_running_on_exception() -> None:
    with patch("shutil.which", return_value="/usr/bin/docker"), patch(
        "subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 10)
    ):
        assert Installer.is_daemon_running() is False

def test_ensure_daemon_running_already_up() -> None:
    with patch.object(Installer, "is_daemon_running", return_value=True):
        assert Installer.ensure_daemon_running() is True

def test_ensure_daemon_running_not_installed() -> None:
    with patch.object(Installer, "is_daemon_running", return_value=False), patch.object(
        Installer, "is_installed", return_value=False
    ):
        assert Installer.ensure_daemon_running() is False

def test_ensure_daemon_running_service_restart_success() -> None:
    mock_res = MagicMock(returncode=0)
    with patch.object(Installer, "is_daemon_running", side_effect=[False, True]), patch.object(
        Installer, "is_installed", return_value=True
    ), patch("subprocess.run", return_value=mock_res):
        assert Installer.ensure_daemon_running() is True

def test_ensure_daemon_running_service_restart_failure() -> None:
    mock_res = MagicMock(returncode=1)
    with patch.object(Installer, "is_daemon_running", return_value=False), patch.object(
        Installer, "is_installed", return_value=True
    ), patch("subprocess.run", return_value=mock_res):
        assert Installer.ensure_daemon_running() is False

def test_ensure_ready_paths() -> None:
    with patch.object(Installer, "is_docker_ready", return_value=True):
        assert Installer.ensure_ready() is True

    with patch.object(Installer, "is_docker_ready", return_value=False), patch.object(
        Installer, "is_installed", return_value=True
    ), patch.object(Installer, "ensure_daemon_running", return_value=True):
        assert Installer.ensure_ready() is True

    with patch.object(Installer, "is_docker_ready", return_value=False), patch.object(
        Installer, "is_installed", return_value=False
    ):
        assert Installer.ensure_ready(auto_install=False) is False

def test_install_docker_already_ready() -> None:
    with patch.object(Installer, "is_docker_ready", return_value=True):
        assert Installer.install_docker() is True

def test_install_docker_success() -> None:
    mock_popen = MagicMock()
    mock_popen.stdout = MagicMock()
    mock_res = MagicMock(returncode=0)
    with patch.object(Installer, "is_docker_ready", return_value=False), patch(
        "subprocess.Popen", return_value=mock_popen
    ), patch("subprocess.run", return_value=mock_res), patch.object(
        Installer, "ensure_daemon_running", return_value=True
    ):
        assert Installer.install_docker() is True
