from __future__ import annotations

import subprocess
import pytest
from src.apps.docker import DockerManager
from src.apps.docker.helpers import ContainerStatus


@pytest.fixture(scope="module", autouse=True)
def ensure_docker_daemon() -> None:
    if not DockerManager.is_docker_available():
        pytest.skip("Docker daemon not running on host machine")


def test_01_image_download_when_missing() -> None:
    mgr = DockerManager()
    mgr.reload_specs()

    image_name = "redis:alpine"
    if mgr.is_image_available(image_name):
        subprocess.run(["docker", "rm", "-f", "movie-redis"], capture_output=True)
        subprocess.run(["docker", "rmi", image_name], capture_output=True)

    assert mgr.is_image_available(image_name) is False

    success = mgr.ensure_running("movie-redis")
    assert success is True
    assert mgr.is_image_available(image_name) is True


def test_02_container_running_and_port_responsive() -> None:
    mgr = DockerManager()
    status = mgr.get_status("movie-redis")

    assert status.status == ContainerStatus.RUNNING
    assert status.is_running is True
    assert status.port_open is True


def test_03_idempotency_prevents_duplicate_deployment() -> None:
    mgr = DockerManager()
    cmd = ["docker", "inspect", "--format", "{{.Id}}", "movie-redis"]
    initial_id = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    assert len(initial_id) > 0

    re_run = mgr.ensure_running("movie-redis")
    assert re_run is True

    subsequent_id = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    assert initial_id == subsequent_id


def test_04_stopped_container_resumed_without_duplicate() -> None:
    mgr = DockerManager()
    stopped = mgr.stop_container("movie-redis")
    assert stopped is True

    status_stopped = mgr.get_status("movie-redis")
    assert status_stopped.is_running is False
    assert status_stopped.status == ContainerStatus.STOPPED

    cmd = ["docker", "inspect", "--format", "{{.Id}}", "movie-redis"]
    orig_id = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

    resumed = mgr.ensure_running("movie-redis")
    assert resumed is True

    status_running = mgr.get_status("movie-redis")
    assert status_running.is_running is True
    assert status_running.status == ContainerStatus.RUNNING
    assert status_running.port_open is True

    new_id = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    assert orig_id == new_id


def test_05_ensure_all_executes_declared_specs() -> None:
    mgr = DockerManager()
    results = mgr.ensure_all()
    assert isinstance(results, dict)
    assert "movie-redis" in results
    assert results["movie-redis"] is True
