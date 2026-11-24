from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.apps.auth import create_token
from src.config import Settings
from src.routers.apps.system import router as system_router
from src.services.apps.system import get_system_service


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(system_router)
    return TestClient(app)


def test_root_endpoint_metadata(app_client: TestClient):
    resp = app_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == Settings.PROJECT_NAME
    assert data["version"] == Settings.VERSION
    assert data["status"] in ("online", "degraded")
    assert "uptime_seconds" in data
    assert "server_time" in data


def test_health_liveness_endpoint(app_client: TestClient):
    resp = app_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "alive")
    assert data["pid"] > 0
    assert "active_jobs" in data
    assert data["version"] == Settings.VERSION

    head_resp = app_client.head("/health")
    assert head_resp.status_code == 200


@pytest.mark.asyncio
async def test_health_readiness_endpoint(app_client: TestClient):
    resp = app_client.get("/health/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert data["status"] in ("ready", "degraded", "unready")
    assert "checks" in data
    assert "database" in data["checks"]
    assert "storage" in data["checks"]
    assert "gpu_governor" in data["checks"]
    assert "network_egress" in data["checks"]
    assert "jobs" in data["checks"]
    assert "version" in data


def test_system_status_dual_guard_access(monkeypatch: pytest.MonkeyPatch, app_client: TestClient):
    app = FastAPI()
    app.include_router(system_router)

    monkeypatch.setattr(Settings, "ENV", "development")
    with TestClient(app) as dev_client:
        assert dev_client.get("/system/status").status_code == 200

    monkeypatch.setattr(Settings, "ENV", "production")
    with TestClient(app, client=("198.51.100.10", 50000)) as remote_client:
        assert remote_client.get("/system/status").status_code == 404

    with TestClient(app, client=("127.0.0.1", 50000)) as local_client:
        assert local_client.get("/system/status", headers={"X-Forwarded-For": "203.0.113.5"}).status_code == 404
        assert local_client.get("/system/status", headers={"X-Real-IP": "203.0.113.5"}).status_code == 404
        assert local_client.get("/system/status").status_code == 200

    admin_token = create_token("u_admin_1", tier="admin", scopes=("admin", "*"))
    with TestClient(app, client=("198.51.100.10", 50000)) as proxied_client:
        headers = {
            "X-Forwarded-For": "203.0.113.5",
            "Authorization": f"Bearer {admin_token}",
        }
        resp = proxied_client.get("/system/status", headers=headers)
        assert resp.status_code == 200

    user_token = create_token("u_reg_1", tier="registered", scopes=())
    with TestClient(app, client=("198.51.100.10", 50000)) as proxied_client:
        headers = {
            "X-Forwarded-For": "203.0.113.5",
            "Authorization": f"Bearer {user_token}",
        }
        resp = proxied_client.get("/system/status", headers=headers)
        assert resp.status_code == 404
