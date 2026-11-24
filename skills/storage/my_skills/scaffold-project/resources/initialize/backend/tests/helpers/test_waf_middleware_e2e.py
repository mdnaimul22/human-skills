import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from src.config import Settings, setup_logger
from src.helpers.middleware import register_middleware
from src.apps.waf import WAFManager

logger = setup_logger(Settings.LOG_DIR / "helpers.log", name="test.waf.middleware")

def create_test_app() -> FastAPI:
    WAFManager.reset_instance()
    app = FastAPI()
    register_middleware(app, logger, Settings)

    @app.get("/api/v1/tools")
    async def sample_endpoint(q: str = ""):
        return JSONResponse({"status": "ok", "q": q})

    @app.get("/api/v1/tools/status/{job_id}")
    async def status_endpoint(job_id: str):
        return JSONResponse({"job_id": job_id, "state": "done"})

    return app

def test_clean_request_allowed():
    app = create_test_app()
    client = TestClient(app)
    resp = client.get("/api/v1/tools", headers={"CF-Connecting-IP": "192.168.1.10"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert "X-Request-ID" in resp.headers

def test_sqli_query_blocked():
    app = create_test_app()
    client = TestClient(app)
    resp = client.get(
        "/api/v1/tools?q=1%20UNION%20SELECT%20null--",
        headers={"CF-Connecting-IP": "185.220.101.50"}
    )
    assert resp.status_code == 403
    assert "Forbidden - Access Denied." in resp.text

def test_scanner_user_agent_blocked():
    app = create_test_app()
    client = TestClient(app)
    resp = client.get(
        "/api/v1/tools",
        headers={"CF-Connecting-IP": "185.220.101.51", "User-Agent": "wafw00f/2.2.0"}
    )
    assert resp.status_code == 403
    assert "Forbidden - Access Denied." in resp.text

def test_rate_limit_exceeded_returns_429():
    app = create_test_app()
    client = TestClient(app)
    bad_ip = "194.26.29.5"
    res = None
    for _ in range(160):
        res = client.get("/api/v1/tools", headers={"CF-Connecting-IP": bad_ip})
        if res.status_code == 429:
            break
    assert res is not None
    assert res.status_code == 429
    assert "Rate Limit Exceeded" in res.text
    assert "Retry-After" in res.headers

def test_tailscale_ip_exempt_from_blocks():
    app = create_test_app()
    client = TestClient(app)
    resp = client.get(
        "/api/v1/tools?q=1%20UNION%20SELECT%20null--",
        headers={"CF-Connecting-IP": "100.64.148.113"}
    )
    assert resp.status_code == 200
