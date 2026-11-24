from __future__ import annotations
from unittest.mock import MagicMock, patch
from src.apps.docker.helpers.container import ContainerEngine, is_port_open
from src.apps.docker.helpers.image import ImagePuller
from src.apps.docker.helpers.schema import ContainerSpec, ContainerStatus

def test_is_port_open() -> None:
    with patch("socket.create_connection", return_value=MagicMock()):
        assert is_port_open(6379) is True
    with patch("socket.create_connection", side_effect=OSError("refused")):
        assert is_port_open(6379) is False

def test_get_state_when_running() -> None:
    mock_res = MagicMock(returncode=0, stdout="true\n")
    with patch("shutil.which", return_value="/usr/bin/docker"), patch(
        "subprocess.run", return_value=mock_res
    ), patch("src.apps.docker.helpers.container.is_port_open", return_value=True):
        state = ContainerEngine.get_state("test-redis", port=6379)
        assert state.status == ContainerStatus.RUNNING
        assert state.is_running is True
        assert state.port_open is True

def test_get_state_when_missing() -> None:
    mock_res = MagicMock(returncode=1, stderr="No such object")
    with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run", return_value=mock_res):
        state = ContainerEngine.get_state("missing-c")
        assert state.status == ContainerStatus.MISSING
        assert state.is_running is False

def test_start_existing_success() -> None:
    mock_res = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_res), patch(
        "src.apps.docker.helpers.container.is_port_open", side_effect=[False, True]
    ), patch("src.apps.docker.helpers.container._sleep_interval"):
        assert ContainerEngine.start_existing("test-c", port=6379) is True

def test_start_existing_cmd_failure() -> None:
    mock_res = MagicMock(returncode=1, stderr="failed")
    with patch("subprocess.run", return_value=mock_res):
        assert ContainerEngine.start_existing("test-c", port=6379) is False

def test_launch_fresh_host_mode() -> None:
    spec = ContainerSpec(
        name="test-pot",
        image="pot:latest",
        port=4416,
        network_mode="host",
        environment={"A": "1"},
        volumes={"/tmp": "/tmp"},
    )
    mock_rm = MagicMock(returncode=0)
    mock_run = MagicMock(returncode=0)
    with patch("subprocess.run", side_effect=[mock_rm, mock_run]) as mock_sub, patch(
        "src.apps.docker.helpers.container.is_port_open", return_value=True
    ), patch("src.apps.docker.helpers.container._sleep_interval"):
        res = ContainerEngine.launch_fresh(spec)
        assert res is True
        calls = mock_sub.call_args_list
        run_args = calls[1][0][0]
        assert "--net" in run_args
        assert "host" in run_args
        assert "-e" in run_args
        assert "A=1" in run_args
        assert "-v" in run_args
        assert "/tmp:/tmp" in run_args

def test_launch_fresh_bridge_mode() -> None:
    spec = ContainerSpec(name="test-redis", image="redis:alpine", port=6379)
    mock_rm = MagicMock(returncode=0)
    mock_run = MagicMock(returncode=0)
    with patch("subprocess.run", side_effect=[mock_rm, mock_run]) as mock_sub, patch(
        "src.apps.docker.helpers.container.is_port_open", return_value=True
    ), patch("src.apps.docker.helpers.container._sleep_interval"):
        res = ContainerEngine.launch_fresh(spec)
        assert res is True
        calls = mock_sub.call_args_list
        run_args = calls[1][0][0]
        assert "-p" in run_args
        assert "127.0.0.1:6379:6379" in run_args

def test_ensure_running_already_open() -> None:
    spec = ContainerSpec(name="test-redis", image="redis:alpine", port=6379)
    image_mgr = ImagePuller()
    with patch("src.apps.docker.helpers.container.is_port_open", return_value=True):
        assert ContainerEngine.ensure_running(spec, image_mgr) is True

def test_ensure_running_triggers_bg_pull_when_configured() -> None:
    spec = ContainerSpec(name="test-bg-spec", image="test:latest", background_pull=True)
    image_mgr = ImagePuller()
    with patch("src.apps.docker.helpers.container.is_port_open", return_value=False), patch.object(
        ContainerEngine, "get_state", return_value=MagicMock(is_running=False, status=ContainerStatus.MISSING)
    ), patch.object(image_mgr, "is_available", return_value=False), patch.object(
        image_mgr, "pull_background"
    ) as mock_bg_pull:
        assert ContainerEngine.ensure_running(spec, image_mgr) is False
        mock_bg_pull.assert_called_once()

def test_stop_and_remove() -> None:
    mock_res = MagicMock(returncode=0)
    with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run", return_value=mock_res):
        assert ContainerEngine.stop("test-c") is True
        assert ContainerEngine.remove("test-c") is True
