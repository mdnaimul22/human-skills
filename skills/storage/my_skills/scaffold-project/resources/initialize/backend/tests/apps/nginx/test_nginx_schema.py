from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.apps.nginx.schema import (
    NGINX_STATE_ADAPTER, NGINX_STATUS_ADAPTER, VHOST_SPEC_ADAPTER,
    NginxState, NginxStatus, VHostSpec,
)


def test_nginx_state_valid() -> None:
    data = {
        "backend_domain": "api.example.com",
        "frontend_domain": "example.com",
        "config_hash": "a1b2c3d4",
        "deployed_files": ["/etc/nginx/sites-available/api.example.com"],
        "last_reloaded_at": "2026-11-14T02:00:00Z",
    }
    state = NGINX_STATE_ADAPTER.validate_python(data)
    assert state.backend_domain == "api.example.com"
    assert state.frontend_domain == "example.com"
    assert state.config_hash == "a1b2c3d4"
    assert len(state.deployed_files) == 1
    assert state.last_reloaded_at == "2026-11-14T02:00:00Z"


def test_nginx_state_validation_failure() -> None:
    with pytest.raises(ValidationError):
        NGINX_STATE_ADAPTER.validate_python({"backend_domain": ""})


def test_nginx_status_defaults() -> None:
    status = NGINX_STATUS_ADAPTER.validate_python({})
    assert status.installed is False
    assert status.running is False
    assert status.backend_domain == ""
    assert status.ssl_enabled is False


def test_vhost_spec_defaults_and_validation() -> None:
    spec = VHOST_SPEC_ADAPTER.validate_python({
        "backend_domain": "api.test.com",
        "frontend_domain": "test.com",
    })
    assert spec.api_port == 8000
    assert spec.rate_limit_zone_size == "10m"
    assert spec.rate_limit_rate == "30r/s"
    assert spec.rate_limit_burst == 50
    assert spec.modsec_enabled is False

    with pytest.raises(ValidationError):
        VHOST_SPEC_ADAPTER.validate_python({
            "backend_domain": "api.test.com",
            "frontend_domain": "test.com",
            "api_port": 999999,
        })
