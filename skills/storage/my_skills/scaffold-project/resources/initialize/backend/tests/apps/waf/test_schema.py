import time
from src.apps.waf.schema import (
    ThreatCategory, RuleMatch, InspectionResult, BanRecord,
    RateLimitDecision, TrafficEntry, WAFStats,
    BAN_RECORD_DICT_ADAPTER, URL_STATUS_DICT_ADAPTER
)

def test_threat_category_enum():
    assert ThreatCategory.SQL_INJECTION.value == "sql_injection"
    assert ThreatCategory.SCANNER.value == "scanner"
    assert ThreatCategory.RATE_LIMIT.value == "rate_limit"

def test_rule_match_serialization():
    match = RuleMatch(
        rule_id="SQLi-1",
        category=ThreatCategory.SQL_INJECTION,
        severity="critical",
        score=80.0,
        pattern_name="union_select"
    )
    assert match.rule_id == "SQLi-1"
    assert match.score == 80.0

def test_inspection_result_defaults():
    res = InspectionResult()
    assert res.decision == "allow"
    assert res.reason == "ok"
    assert res.score == 0.0
    assert res.threat_category == ThreatCategory.UNKNOWN
    assert res.matched_rules == []
    assert res.indicators == {}

def test_ban_record_adapter():
    data = {
        "192.168.1.1": {
            "ip": "192.168.1.1",
            "strikes": 3,
            "banned_until": 1700000000.0,
            "reason": "/etc/passwd",
            "created_at": 1699990000.0
        }
    }
    validated = BAN_RECORD_DICT_ADAPTER.validate_python(data)
    assert "192.168.1.1" in validated
    assert validated["192.168.1.1"].strikes == 3

def test_url_status_adapter():
    data = {"/api/v1/tools": 200, "/forbidden": 403}
    validated = URL_STATUS_DICT_ADAPTER.validate_python(data)
    assert validated["/forbidden"] == 403

def test_rate_limit_decision_and_stats():
    rld = RateLimitDecision(allowed=True, remaining_tokens=59.5, reset_seconds=0.5, limit_rpm=60)
    assert rld.allowed is True
    stats = WAFStats(
        total_requests=10, total_allowed=8, total_blocked=2,
        total_rate_limited=1, active_bans_count=1,
        by_threat_category={"sql_injection": 1},
        by_rule={"SQLi-1": 1},
        uptime_seconds=100.0, requests_per_minute=6.0, block_rate_percent=20.0
    )
    assert stats.total_requests == 10
