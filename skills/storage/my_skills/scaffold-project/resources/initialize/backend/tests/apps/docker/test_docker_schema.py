from __future__ import annotations
import pytest
from pydantic import ValidationError
from src.apps.docker.helpers.schema import (
    ContainerSpec,
    ContainerState,
    ContainerStatus,
    CONTAINER_SPECS_ADAPTER,
    CONTAINER_SPEC_ADAPTER,
)

def test_container_spec_defaults() -> None:
    spec = ContainerSpec(name="test-redis", image="redis:alpine")
    assert spec.name == "test-redis"
    assert spec.image == "redis:alpine"
    assert spec.port is None
    assert spec.host_port is None
    assert spec.bind_ip == "127.0.0.1"
    assert spec.network_mode == "bridge"
    assert spec.restart_policy == "always"
    assert spec.enabled is True
    assert spec.background_pull is False
    assert spec.environment == {}
    assert spec.volumes == {}

def test_container_spec_custom_fields() -> None:
    spec = ContainerSpec(
        name="movie-pot",
        image="provider:latest",
        port=4416,
        network_mode="host",
        environment={"KEY": "VAL"},
        volumes={"/data": "/data"},
        enabled=False,
        background_pull=True,
    )
    assert spec.port == 4416
    assert spec.network_mode == "host"
    assert spec.environment["KEY"] == "VAL"
    assert spec.volumes["/data"] == "/data"
    assert spec.enabled is False
    assert spec.background_pull is True

def test_container_spec_validation_failure() -> None:
    with pytest.raises(ValidationError):
        ContainerSpec(name="", image="valid:image")

    with pytest.raises(ValidationError):
        ContainerSpec(name="valid", image="")

def test_container_specs_adapter_valid_list() -> None:
    payload = [
        {"name": "c1", "image": "img1", "port": 8080},
        {"name": "c2", "image": "img2", "network_mode": "host"},
    ]
    specs = CONTAINER_SPECS_ADAPTER.validate_python(payload)
    assert len(specs) == 2
    assert specs[0].name == "c1"
    assert specs[0].port == 8080
    assert specs[1].network_mode == "host"

def test_container_state_properties() -> None:
    state = ContainerState(
        name="test-c",
        status=ContainerStatus.RUNNING,
        port_open=True,
        is_running=True,
        details="Healthy",
    )
    assert state.name == "test-c"
    assert state.status == ContainerStatus.RUNNING
    assert state.port_open is True
    assert state.is_running is True
    assert state.details == "Healthy"
