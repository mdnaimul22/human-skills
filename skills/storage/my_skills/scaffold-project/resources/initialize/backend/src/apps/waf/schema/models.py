from enum import Enum
from pydantic import BaseModel, Field, TypeAdapter

class ThreatCategory(str, Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    RCE = "remote_code_execution"
    SSRF = "server_side_request_forgery"
    XXE = "xml_external_entity"
    LFI = "local_file_inclusion"
    SCANNER = "scanner"
    ANOMALY = "anomaly"
    RATE_LIMIT = "rate_limit"
    HONEYPOT = "honeypot"
    UNKNOWN = "unknown"

class RuleMatch(BaseModel):
    rule_id: str
    category: ThreatCategory
    severity: str
    score: float
    pattern_name: str

class InspectionResult(BaseModel):
    decision: str = "allow"
    reason: str = "ok"
    score: float = 0.0
    threat_category: ThreatCategory = ThreatCategory.UNKNOWN
    matched_rules: list[str] = Field(default_factory=list)
    indicators: dict[str, float] = Field(default_factory=dict)

class BanRecord(BaseModel):
    ip: str = ""
    strikes: int = 0
    banned_until: float = 0.0
    reason: str = ""
    created_at: float = 0.0

class RateLimitDecision(BaseModel):
    allowed: bool
    remaining_tokens: float
    reset_seconds: float
    limit_rpm: int

class TrafficEntry(BaseModel):
    timestamp: float
    method: str
    path: str
    client_ip: str
    user_agent: str
    decision: str
    reason: str
    score: float
    threat_category: str
    status_code: int
    latency_ms: float

class WAFStats(BaseModel):
    total_requests: int
    total_allowed: int
    total_blocked: int
    total_rate_limited: int
    active_bans_count: int
    by_threat_category: dict[str, int]
    by_rule: dict[str, int]
    uptime_seconds: float
    requests_per_minute: float
    block_rate_percent: float

BAN_RECORD_DICT_ADAPTER = TypeAdapter(dict[str, BanRecord])
URL_STATUS_DICT_ADAPTER = TypeAdapter(dict[str, int])
