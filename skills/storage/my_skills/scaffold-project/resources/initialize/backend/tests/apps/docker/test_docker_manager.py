from __future__ import annotations
from unittest.mock import MagicMock, patch
from src.apps.docker import DockerManager, get_docker_manager
from src.apps.docker.helpers.schema import ContainerSpec, ContainerState, ContainerStatus

def setup_function() -> None:
    DockerManager.reset_instance()

def test_singleton_instance() -> None:
    m1 = DockerManager()
    m2 = get_docker_manager()
    assert m1 is m2

def test_reload_specs_missing_file() -> None:
    with patch("src.apps.docker.manager.exists", return_value=False), patch(
        "src.apps.docker.manager.write_json"
    ) as mock_write:
        mgr = DockerManager()
        assert mgr._specs == {}
        mock_write.assert_called_once_with("data/apps/docker/containers.json", [])

def test_reload_specs_valid() -> None:
    sample_data = [
        {"name": "c1", "image": "img1", "port": 8000, "enabled": True},
        {"name": "c2", "image": "img2", "port": 9000, "enabled": False},
    ]
    with patch("src.apps.docker.manager.exists", return_value=True), patch(
        "src.apps.docker.manager.read_json", return_value=sample_data
    ):
        mgr = DockerManager()
        mgr.reload_specs()
        assert "c1" in mgr._specs
        assert "c2" not in mgr._specs
        assert mgr.get_spec("c1") is not None
        assert mgr.get_spec("unknown") is None

def test_ensure_running_unknown_spec() -> None:
    mgr = DockerManager()
    assert mgr.ensure_running("non_existent") is False

def test_ensure_running_installer_not_ready() -> None:
    mgr = DockerManager()
    mgr._specs["dummy"] = ContainerSpec(name="dummy", image="dummy:latest")
    with patch.object(mgr._installer, "ensure_ready", return_value=False):
        assert mgr.ensure_running("dummy") is False

def test_ensure_running_success() -> None:
    mgr = DockerManager()
    mgr._specs["dummy"] = ContainerSpec(name="dummy", image="dummy:latest", port=9999)
    with patch.object(mgr._installer, "ensure_ready", return_value=True), patch.object(
        mgr._engine, "ensure_running", return_value=True
    ):
        assert mgr.ensure_running("dummy") is True
        assert "dummy" in mgr._started_by_us

def test_ensure_all() -> None:
    mgr = DockerManager()
    mgr._specs = {
        "c1": ContainerSpec(name="c1", image="img1"),
        "c2": ContainerSpec(name="c2", image="img2"),
    }
    with patch.object(mgr, "ensure_running", side_effect=[True, False]):
        results = mgr.ensure_all()
        assert results == {"c1": True, "c2": False}

def test_stop_container_and_stop_all() -> None:
    mgr = DockerManager()
    mgr._started_by_us.add("c1")
    mgr._started_by_us.add("c2")
    with patch.object(mgr._engine, "stop", return_value=True):
        assert mgr.stop_container("c1") is True
        assert "c1" not in mgr._started_by_us
        mgr.stop_all()
        assert len(mgr._started_by_us) == 0

def test_get_status() -> None:
    mgr = DockerManager()
    mock_state = ContainerState(
        name="test-c",
        status=ContainerStatus.RUNNING,
        port_open=True,
        is_running=True,
    )
    with patch.object(mgr._engine, "get_state", return_value=mock_state):
        state = mgr.get_status("test-c")
        assert state.status == ContainerStatus.RUNNING
        assert state.is_running is True

def test_image_helpers() -> None:
    mgr = DockerManager()
    with patch.object(mgr._images, "is_available", return_value=True) as mock_avail, \
         patch.object(mgr._images, "pull_background") as mock_pull:
        assert mgr.is_image_available("redis:alpine") is True
        mock_avail.assert_called_with("redis:alpine")

        mgr.trigger_background_pull("redis:alpine")
        mock_pull.assert_called_with("redis:alpine", on_complete=None)
