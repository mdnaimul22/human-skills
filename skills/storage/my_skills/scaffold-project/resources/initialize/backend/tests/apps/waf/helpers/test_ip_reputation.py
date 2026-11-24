import time
import uuid
import pytest
from src.config import delete, ensure_dir
from src.apps.waf.helpers.ip_reputation import IPReputationManager


@pytest.fixture
def sandbox_dir() -> str:
    rel = f"tmp/test_tmp/waf_ip_{uuid.uuid4().hex[:8]}"
    ensure_dir(rel)
    try:
        yield rel
    finally:
        delete(rel)


def test_whitelist_loopback_and_tailscale(sandbox_dir: str):
    mgr = IPReputationManager(storage_path=f"{sandbox_dir}/blacklist.json")
    assert mgr.is_whitelisted("127.0.0.1") is True
    assert mgr.is_whitelisted("::1") is True
    assert mgr.is_whitelisted("100.80.50.87") is True
    assert mgr.is_whitelisted("100.64.148.113") is True
    assert mgr.is_whitelisted("192.168.1.50") is True
    assert mgr.is_whitelisted("185.220.101.5") is False

def test_strike_and_ban_lifecycle(sandbox_dir: str):
    mgr = IPReputationManager(storage_path=f"{sandbox_dir}/blacklist.json")
    bad_ip = "185.220.101.5"
    assert mgr.is_banned(bad_ip) is False
    
    banned = mgr.record_threat(bad_ip, "sqli probe", strikes=1)
    assert banned is False
    assert mgr.is_banned(bad_ip) is False

    banned = mgr.record_threat(bad_ip, "sqli probe", strikes=2)
    assert banned is True
    assert mgr.is_banned(bad_ip) is True
    assert mgr.active_bans_count() == 1

def test_critical_threat_immediate_ban(sandbox_dir: str):
    mgr = IPReputationManager(storage_path=f"{sandbox_dir}/blacklist.json")
    evil_ip = "45.154.255.89"
    banned = mgr.record_threat(evil_ip, "rce execution", strikes=1, critical=True)
    assert banned is True
    assert mgr.is_banned(evil_ip) is True

def test_unban_and_flush_persistence(sandbox_dir: str):
    path = f"{sandbox_dir}/blacklist.json"
    mgr = IPReputationManager(storage_path=path)
    target_ip = "99.88.77.66"
    mgr.ban(target_ip, duration_seconds=100.0, reason="manual test")
    assert mgr.is_banned(target_ip) is True
    mgr.flush()

    mgr2 = IPReputationManager(storage_path=path)
    assert mgr2.is_banned(target_ip) is True

    unbanned = mgr2.unban(target_ip)
    assert unbanned is True
    assert mgr2.is_banned(target_ip) is False

def test_cleanup_expired(sandbox_dir: str):
    mgr = IPReputationManager(storage_path=f"{sandbox_dir}/blacklist.json")
    ip = "11.22.33.44"
    mgr.ban(ip, duration_seconds=0.01, reason="quick ban")
    time.sleep(0.02)
    expired, _ = mgr.cleanup_expired()
    assert expired == 1
    assert mgr.is_banned(ip) is False
