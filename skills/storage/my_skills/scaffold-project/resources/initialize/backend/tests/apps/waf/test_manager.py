import pytest
import asyncio
from src.apps.waf import WAFManager
from src.apps.waf.schema import ThreatCategory

@pytest.fixture(autouse=True)
def reset_waf_singleton():
    WAFManager.reset_instance()
    yield
    WAFManager.reset_instance()

@pytest.mark.asyncio
async def test_waf_manager_whitelist_pass():
    waf = WAFManager()
    result = await waf.inspect("127.0.0.1", "/anything/malicious/<script>")
    assert result.decision == "allow"
    assert result.reason == "whitelisted"

@pytest.mark.asyncio
async def test_waf_manager_block_sqli():
    waf = WAFManager()
    attacker_ip = "185.220.101.5"
    result = await waf.inspect(attacker_ip, "/api/v1/tools", query="q=1' UNION SELECT null--")
    assert result.decision == "block"
    assert "SQLi-1" in result.reason
    assert result.threat_category == ThreatCategory.SQL_INJECTION

@pytest.mark.asyncio
async def test_waf_manager_block_scanner_ua():
    waf = WAFManager()
    attacker_ip = "185.220.101.6"
    headers = {"user-agent": "wafw00f/2.2.0"}
    result = await waf.inspect(attacker_ip, "/api/v1/tools", headers=headers)
    assert result.decision == "block"
    assert "SCANNER-1" in result.reason
    assert result.threat_category == ThreatCategory.SCANNER

@pytest.mark.asyncio
async def test_waf_manager_rate_limit():
    waf = WAFManager()
    ip = "45.154.255.10"
    res = None
    for _ in range(160):
        res = await waf.inspect(ip, "/api/v1/tools")
        if res.decision == "rate_limit":
            break
    assert res is not None
    assert res.decision == "rate_limit"
    assert res.threat_category == ThreatCategory.RATE_LIMIT

@pytest.mark.asyncio
async def test_waf_manager_anomaly_block():
    waf = WAFManager()
    ip = "194.26.29.111"
    res = await waf.inspect(
        ip, "/etc/passwd",
        query="payload=%27%20OR%201=1--%00",
        headers={"x-original-url": "/admin"}
    )
    assert res.decision == "block"
    assert res.score >= 50.0

@pytest.mark.asyncio
async def test_waf_manager_lifecycle():
    waf = WAFManager()
    waf.start_flush_task()
    assert waf._bg_task is not None
    await waf.shutdown()
    assert waf._bg_task.done() is True

def test_waf_manager_is_allowed_path():
    waf = WAFManager(allowed_prefixes=("/custom/", "/health"))
    assert waf.is_allowed_path("/") is True
    assert waf.is_allowed_path("/custom/app") is True
    assert waf.is_allowed_path("/health") is True
    assert waf.is_allowed_path("/unregistered/route") is False
