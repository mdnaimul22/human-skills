import time
from src.apps.waf.schema import TrafficEntry
from src.apps.waf.helpers.traffic_store import TrafficStore

def test_traffic_store_entry_and_stats(tmp_path):
    store = TrafficStore(storage_path=f"{tmp_path}/requested_url.json")
    entry = TrafficEntry(
        timestamp=time.time(),
        method="GET",
        path="/api/v1/tools",
        client_ip="1.2.3.4",
        user_agent="Mozilla",
        decision="allow",
        reason="ok",
        score=0.0,
        threat_category="unknown",
        status_code=200,
        latency_ms=1.5,
    )
    store.record_entry(entry)
    stats = store.get_stats(active_bans=0)
    assert stats.total_requests == 1
    assert stats.total_allowed == 1
    assert stats.total_blocked == 0

def test_blocked_and_threat_stats(tmp_path):
    store = TrafficStore(storage_path=f"{tmp_path}/requested_url.json")
    entry = TrafficEntry(
        timestamp=time.time(),
        method="POST",
        path="/api/v1/tools",
        client_ip="5.6.7.8",
        user_agent="sqlmap",
        decision="block",
        reason="rule:SQLi-1",
        score=80.0,
        threat_category="sql_injection",
        status_code=403,
        latency_ms=0.5,
    )
    store.record_entry(entry)
    stats = store.get_stats(active_bans=1)
    assert stats.total_requests == 1
    assert stats.total_blocked == 1
    assert stats.by_threat_category.get("sql_injection") == 1
    assert stats.by_rule.get("SQLi-1") == 1

def test_track_url_persistence(tmp_path):
    path = f"{tmp_path}/requested_url.json"
    store = TrafficStore(storage_path=path)
    store.track_url("/api/v1/tools", 200)
    store.track_url("/honeypot.php", 403)
    store.flush()

    store2 = TrafficStore(storage_path=path)
    assert store2._requested_urls.get("/honeypot.php") == 403
