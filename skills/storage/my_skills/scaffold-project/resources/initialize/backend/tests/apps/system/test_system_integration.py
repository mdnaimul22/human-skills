from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.apps.system import SystemManager, UserTier
from src.config import Settings
from src.routers.apps.system import router as system_router


@pytest.fixture(autouse=True)
def _reset_managers() -> None:
    SystemManager.reset_instance()
    yield
    SystemManager.reset_instance()


def test_system_status_router_dev_and_localhost_only_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    app.include_router(system_router)
    client = TestClient(app)

    monkeypatch.setattr(Settings, "ENV", "development")
    dev_resp = client.get("/system/status")
    assert dev_resp.status_code == 200
    body = dev_resp.json()
    assert body["hardware"]["cpu"]["logical_cores"] >= 1
    assert body["budget"]["usable_cpu_threads"] >= 1
    assert body["active_limits"]["SYSTEM_MAX_CPU_USAGE_PERCENT"] == Settings.SYSTEM_MAX_CPU_USAGE_PERCENT

    monkeypatch.setattr(Settings, "ENV", "production")
    with TestClient(app, client=("198.51.100.10", 50000)) as remote_client:
        assert remote_client.get("/system/status").status_code == 404

    with TestClient(app, client=("127.0.0.1", 50000)) as local_client:
        assert local_client.get("/system/status", headers={"X-Forwarded-For": "203.0.113.5"}).status_code == 404
        assert local_client.get("/system/status", headers={"X-Real-IP": "203.0.113.5"}).status_code == 404
        direct_resp = local_client.get("/system/status")
        assert direct_resp.status_code == 200


@pytest.mark.asyncio
async def test_circuit_breaker_fallback_permit() -> None:
    sm = SystemManager.get_instance()
    await sm.start_async()
    try:
        for _ in range(Settings.SYSTEM_BREAKER_FAILURE_THRESHOLD):
            sm.notify_hardware_anomaly("h264_nvenc", "simulated hardware failure")

        fallback_permit = await sm.acquire_resource_permit("encode", "j_cpu_fb", user_tier=UserTier.PREMIUM, timeout=5.0)
        try:
            assert fallback_permit.gpu_enabled is False
            assert fallback_permit.hwaccel == "cpu"
            assert fallback_permit.gpu_downgrade_reason is not None
        finally:
            sm.release_resource_permit(fallback_permit)
    finally:
        await sm.stop_async()
