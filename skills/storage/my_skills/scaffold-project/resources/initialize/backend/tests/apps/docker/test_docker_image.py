from __future__ import annotations
import time
from unittest.mock import MagicMock, patch
from src.apps.docker.helpers.image import ImagePuller

def test_is_available_when_cached() -> None:
    puller = ImagePuller()
    mock_res = MagicMock(returncode=0)
    with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run", return_value=mock_res):
        assert puller.is_available("redis:alpine") is True

def test_is_available_when_missing() -> None:
    puller = ImagePuller()
    mock_res = MagicMock(returncode=1)
    with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run", return_value=mock_res):
        assert puller.is_available("redis:alpine") is False

def test_is_available_without_docker() -> None:
    puller = ImagePuller()
    with patch("shutil.which", return_value=None):
        assert puller.is_available("redis:alpine") is False

def test_pull_already_available() -> None:
    puller = ImagePuller()
    with patch.object(puller, "is_available", return_value=True):
        assert puller.pull("redis:alpine") is True

def test_pull_success() -> None:
    puller = ImagePuller()
    mock_res = MagicMock(returncode=0)
    with patch.object(puller, "is_available", return_value=False), patch("subprocess.run", return_value=mock_res):
        assert puller.pull("redis:alpine") is True

def test_pull_failure() -> None:
    puller = ImagePuller()
    mock_res = MagicMock(returncode=1, stderr="network timeout")
    with patch.object(puller, "is_available", return_value=False), patch("subprocess.run", return_value=mock_res):
        assert puller.pull("redis:alpine") is False

def test_pull_background_lifecycle() -> None:
    puller = ImagePuller()
    called = []
    def callback() -> None:
        called.append(True)

    mock_res = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_res):
        puller.pull_background("test:image", on_complete=callback)
        time.sleep(0.1)

    assert len(called) == 1
    assert puller.is_pulling("test:image") is False

def test_pull_background_deduplication() -> None:
    puller = ImagePuller()
    puller._pulling_images.add("duplicate:image")
    with patch("threading.Thread") as mock_thread:
        puller.pull_background("duplicate:image")
        mock_thread.assert_not_called()
