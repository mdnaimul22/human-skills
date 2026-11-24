from src.apps.waf.helpers.rule_engine import RuleEngine
from src.apps.waf.schema import ThreatCategory

def test_allowed_paths():
    engine = RuleEngine()
    assert engine.is_allowed_path("/") is True
    assert engine.is_allowed_path("/api/v1/tools") is True
    assert engine.is_allowed_path("/_next/static/chunk.js") is True
    assert engine.is_allowed_path("/wp-admin") is False
    assert engine.is_allowed_path("/unknown/route") is False

def test_match_sqli():
    engine = RuleEngine()
    matches = engine.match("GET /api/v1/tools?q=1%20UNION%20SELECT%20null--")
    assert any(m.rule_id == "SQLi-1" and m.category == ThreatCategory.SQL_INJECTION for m in matches)

def test_match_xss():
    engine = RuleEngine()
    matches = engine.match("POST /api/v1/tools <script>alert(1)</script>")
    assert any(m.rule_id == "XSS-1" and m.category == ThreatCategory.XSS for m in matches)

def test_match_command_injection():
    engine = RuleEngine()
    matches = engine.match("GET /api/v1/tools?cmd=;whoami")
    assert any(m.rule_id == "CMD-1" and m.category == ThreatCategory.COMMAND_INJECTION for m in matches)

def test_match_path_traversal():
    engine = RuleEngine()
    matches = engine.match("GET /api/v1/../../etc/passwd")
    assert any(m.rule_id == "PATH-1" and m.category == ThreatCategory.PATH_TRAVERSAL for m in matches)

def test_match_scanner_user_agent():
    engine = RuleEngine()
    matches = engine.match("GET /api/v1/tools user-agent:wafw00f/2.1.0")
    assert any(m.rule_id == "SCANNER-1" and m.category == ThreatCategory.SCANNER for m in matches)

def test_match_honeypot():
    engine = RuleEngine()
    matches = engine.match("GET /wp-login.php")
    assert any(m.rule_id == "HONEYPOT-1" and m.category == ThreatCategory.HONEYPOT for m in matches)

def test_match_clean_request():
    engine = RuleEngine()
    matches = engine.match("GET /api/v1/tools/status/12345 Mozilla/5.0")
    assert len(matches) == 0
