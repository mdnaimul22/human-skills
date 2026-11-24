from src.apps.waf.helpers.anomaly import AnomalyScorer

def test_clean_request_zero_score():
    scorer = AnomalyScorer(threshold=50.0)
    score, indicators, is_anomaly = scorer.score("GET", "/api/v1/tools", "", {"user-agent": "Mozilla/5.0"})
    assert score == 0.0
    assert len(indicators) == 0
    assert is_anomaly is False

def test_unusual_http_method():
    scorer = AnomalyScorer(threshold=50.0)
    score, indicators, is_anomaly = scorer.score("DEBUG", "/api/v1/tools", "", {})
    assert score == 20.0
    assert "unusual_method" in indicators
    assert is_anomaly is False

def test_sql_plus_encoded_exceeds_threshold():
    scorer = AnomalyScorer(threshold=50.0)
    score, indicators, is_anomaly = scorer.score(
        "GET", "/api/v1/tools", "q=select%20*%20from%20users%20where%201=1", {}
    )
    assert score >= 50.0
    assert "sql_indicator" in indicators
    assert "encoded_payload" in indicators
    assert is_anomaly is True

def test_path_traversal_anomaly():
    scorer = AnomalyScorer(threshold=40.0)
    score, indicators, is_anomaly = scorer.score("GET", "/etc/passwd", "", {})
    assert score >= 40.0
    assert "traversal_indicator" in indicators
    assert is_anomaly is True

def test_suspicious_header_indicator():
    scorer = AnomalyScorer(threshold=50.0)
    score, indicators, _ = scorer.score("GET", "/api/v1/tools", "", {"x-original-url": "/admin"})
    assert "suspicious_header" in indicators
