from __future__ import annotations

from unittest.mock import MagicMock, patch
from src.apps.nginx.helpers.deployer import Deployer


def test_clean_old_deletes_paths() -> None:
    mock_run = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_run) as mock_cmd, patch(
        "src.apps.nginx.helpers.deployer.exists", return_value=True
    ), patch("src.apps.nginx.helpers.deployer.delete") as mock_delete:
        Deployer.clean_old("old_api.xyz", "old_front.xyz")
        assert mock_cmd.call_count >= 1
        assert mock_delete.call_count >= 1


def test_clean_old_handles_exception() -> None:
    with patch("subprocess.run", side_effect=RuntimeError("error")):
        Deployer.clean_old("old_api.xyz", "old_front.xyz")


def test_deploy_success() -> None:
    mock_run = MagicMock(returncode=0)
    with patch("src.apps.nginx.helpers.deployer.exists", return_value=True), patch(
        "subprocess.run", return_value=mock_run
    ) as mock_cmd:
        assert Deployer.deploy() is True
        assert mock_cmd.call_count == 5


def test_deploy_fails_if_source_missing() -> None:
    with patch("src.apps.nginx.helpers.deployer.exists", return_value=False):
        assert Deployer.deploy() is False


def test_deploy_fails_on_copy_error() -> None:
    mock_run = MagicMock(returncode=1, stderr="permission denied")
    with patch("src.apps.nginx.helpers.deployer.exists", return_value=True), patch(
        "subprocess.run", return_value=mock_run
    ):
        assert Deployer.deploy() is False


def test_deploy_fails_on_symlink_error() -> None:
    mock_copy = MagicMock(returncode=0)
    mock_link = MagicMock(returncode=1, stderr="link error")
    with patch("src.apps.nginx.helpers.deployer.exists", return_value=True), patch(
        "subprocess.run", side_effect=[mock_copy, mock_copy, mock_copy, mock_link]
    ):
        assert Deployer.deploy() is False


def test_deploy_catches_exception() -> None:
    with patch("src.apps.nginx.helpers.deployer.exists", side_effect=RuntimeError("crash")):
        assert Deployer.deploy() is False
