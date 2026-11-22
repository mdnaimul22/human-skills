# waf.py DOX

> *`src/apps/waf/` acts as the "Security Perimeter & Firewall Gateway":*
> *It sits in front of application HTTP handlers to inspect inbound requests across multiple attack vectors (SQLi, XSS, RCE, traversal, scanners, anomalies).*
> *It operates completely independently of domain business logic, allowing any application middleware to enforce zero-trust security and adaptive rate limiting.*

## Purpose

- Own the `src/apps/waf` Web Application Firewall and security telemetry substrate.
- Provide multi-layered perimeter defense against OWASP Top 10 threats, automated scanners, path traversals, and anomalous traffic patterns.
- Enforce token-bucket sliding-window rate limiting with adaptive burst capacities for high-frequency video polling and static asset routes.
- Manage IP reputation, CIDR-based network whitelisting (including Tailscale mesh network `100.64.0.0/10`), progressive threat strike tracking, and persistent bans.
- Maintain circular in-memory traffic telemetry buffers and persist endpoint access statistics to disk.
- Keep this module-level DOX profile synchronized with `src/apps/waf/` implementation files.

## Ownership

- `src/apps/waf/manager.py` owns the public orchestrator and consumer contract (`WAFManager`).
- `src/apps/waf/helpers/` owns the isolated sub-engine worker implementations ("internal machinery").
- `src/apps/waf/schema/` owns all Pydantic v2 data contracts and TypeAdapters.
- `src/apps/waf/__init__.py` owns PEP 562 lazy exports (`_LAZY_EXPORTS`, `__getattr__`).
- `waf.py.mdx.md` owns durable notes about responsibilities, runtime contracts, side effects, key concepts, work guidance, and verification.
- **Classes:**
  - `WAFManager` (Public Facade / Orchestrator)
    - `is_banned(self, ip: str) -> bool`
    - `is_whitelisted(self, ip: str) -> bool`
    - `is_allowed_path(self, path: str) -> bool`
    - `start_flush_task(self) -> None`
    - `async shutdown(self) -> None`
    - `async inspect(self, ip: str, path: str, query: str = "", headers: dict[str, str] | None = None, method: str = "GET") -> InspectionResult`
    - `async check_request(self, ip: str, path: str, query: str = "", headers: dict[str, str] | None = None, method: str = "GET") -> bool`
    - `async track_url(self, path: str, status_code: int) -> None`
    - `record_traffic(self, method: str, path: str, client_ip: str, user_agent: str, decision: str, reason: str, score: float, threat_category: str, status_code: int, latency_ms: float) -> None`
    - `get_stats(self) -> WAFStats`
    - `ban_ip(self, ip: str, duration_seconds: float, reason: str) -> None`
    - `unban_ip(self, ip: str) -> bool`
    - `reset_instance(cls) -> None`
  - `RuleEngine` (`helpers/rule_engine.py`)
    - Precompiled regex matching for OWASP attack signatures and route prefix validation.
    - `match(self, payload: str) -> list[RuleMatch]`
    - `is_allowed_path(self, path: str) -> bool`
  - `AnomalyScorer` (`helpers/anomaly.py`)
    - Multi-factor heuristic anomaly scoring across methods, path fragments, encodings, and HTTP headers.
    - `score(self, method: str, path: str, query: str, headers: dict[str, str]) -> tuple[float, list[str], bool]`
  - `TokenBucketRateLimiter` (`helpers/rate_limiter.py`)
    - Sliding-window token bucket limiter with path-aware burst capacity.
    - `check(self, ip: str, path: str) -> RateLimitDecision`
    - `cleanup_stale(self, max_idle: float = 300.0) -> int`
  - `IPReputationManager` (`helpers/ip_reputation.py`)
    - Subnet whitelisting, threat strike recording, progressive exponential bans, and disk synchronization.
    - `is_whitelisted(self, ip: str) -> bool`
    - `is_banned(self, ip: str) -> bool`
    - `record_threat(self, ip: str, threat: str, strikes: int = 1, critical: bool = False) -> None`
    - `ban(self, ip: str, duration_seconds: float, reason: str) -> None`
    - `unban(self, ip: str) -> bool`
    - `active_bans_count(self) -> int`
    - `cleanup_expired(self) -> int`
    - `flush(self) -> None`
  - `TrafficStore` (`helpers/traffic_store.py`)
    - In-memory circular buffer of traffic entries and persistent URL status tracking.
    - `record_entry(self, entry: TrafficEntry) -> None`
    - `track_url(self, path: str, status_code: int) -> None`
    - `get_stats(self, active_bans: int) -> WAFStats`
    - `flush(self) -> None`
- **Data Contracts (`src/apps/waf/schema/models.py`):**
  - `ThreatCategory` (Enum of attack classifications: SQLi, XSS, RCE, SSRF, XXE, LFI, Scanners, Rate Limit, etc.)
  - `RuleMatch` (Model representing an individual regex trigger: rule_id, category, severity, score)
  - `InspectionResult` (Decision model returned to caller: allow, block, rate_limit, score, indicators)
  - `BanRecord` (Model for active IP bans: ip, reason, banned_at, expires_at)
  - `RateLimitDecision` (Model for rate limit decisions: allowed, tokens_remaining, reset_seconds)
  - `TrafficEntry` (Ring-buffer telemetry record for inbound HTTP requests)
  - `WAFStats` (Aggregated metrics model: total_requests, blocked_requests, rate_limited, active_bans)
- **Notable Constants/Configurations:**
  - `_FLUSH_INTERVAL_SECONDS = 30.0`
  - `_STANDARD_CAPACITY = 120.0`, `_STANDARD_REFILL_RATE = 2.0` (tokens/sec)
  - `_HIGH_CAPACITY = 300.0`, `_HIGH_REFILL_RATE = 10.0` (tokens/sec)
  - `_ANOMALY_THRESHOLD = 50.0`
  - `_TRUSTED_NETWORKS = 100.64.0.0/10` (Tailscale), `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`

## Runtime Contracts

- **Singleton Pattern:** External callers instantiate `WAFManager()` which yields a singleton instance via `__new__`.
- **Preemptive Whitelist Bypass:** Any request originating from loopback (`127.0.0.1`, `::1`) or the Tailscale mesh CIDR (`100.64.0.0/10`) immediately returns an `allow` decision, bypassing rule matching and rate limits.
- **Ordered Multi-Tier Inspection Pipeline:**
  1. *Subnet Whitelist Gate:* Checks whether client IP belongs to trusted CIDR blocks.
  2. *Active Ban Gate:* Verifies against active IP ban table (drops immediately with `block` if banned).
  3. *Rate Limit Gate:* Verifies token bucket capacity; returns `rate_limit` decision (`HTTP 429`) and registers threat strike upon exhaustion.
  4. *Rule Engine Gate:* Matches normalized request signature (`method`, `path`, `query`, `user-agent`) against precompiled regex rules. Drops with `block` (`HTTP 403`) upon high/critical severity matches.
  5. *Anomaly Scorer Gate:* Aggregates heuristic scores for unusual verbs, multi-factor injections, and suspicious headers. Drops with `block` if score $\ge 50.0$.
  6. *Route Whitelist Gate:* Verifies path against registered application route prefixes (`_ALLOWED_PREFIXES`).
- **Strike & Ban Escalation Invariants:**
  - Standard rule matches increment strike counters by 1.
  - Honeypot and scanner triggers immediately add 3 strikes.
  - Critical vulnerabilities (e.g. RCE) or 3 accumulated strikes trigger an immediate progressive IP ban (1 hour initially, 24 hours on recidivism).
- **Periodic Background Durability:** Active bans and telemetry data flush atomically to `data/waf/blacklist.json` and `data/waf/requested_url.json` every 30 seconds via `_periodic_flush()`.
- **Observed Side-Effect Areas:**
  - Atomic JSON writes to `data/waf/blacklist.json` and `data/waf/requested_url.json`.
  - Structured rotating logs to `logs/waf.log`.
  - Memory consumption constrained via `collections.deque(maxlen=1000)` ring buffer.
- **Imported Dependency Areas:**
  - `src.config` (Settings, setup_logger, path utilities, set_telemetry_context).
  - `pydantic` (BaseModel, Field, TypeAdapter).

## Key Concepts

- **Perimeter Defense Substrate:**
  - Decoupled from application business logic: acts solely as an HTTP traffic validator.
  - Fast execution: regex matching and token checks execute in sub-millisecond in-memory operations.
- **Sub-Engine Isolation ("Internal Machinery"):**
  - All worker components (`RuleEngine`, `AnomalyScorer`, `TokenBucketRateLimiter`, `IPReputationManager`, `TrafficStore`) reside strictly in `src/apps/waf/helpers/`.
  - External modules never import private helpers directly; they only consume `from src.apps.waf import WAFManager`.
- **Consumer Middleware Contract:**
  - Integrated cleanly inside HTTP middleware (e.g. `src/helpers/middleware.py`).
  - Request inspection happens before route handlers execute, returning `HTTP 403 Forbidden` for blocked threats or `HTTP 429 Too Many Requests` for exhausted token buckets.

## Work Guidance

- Never expose or import `src/apps/waf/helpers/*` outside of `src/apps/waf/`.
- Maintain strict type safety across all helper methods without using `Any` or `isinstance` branching.
- Keep the regex rule table (`_RULES`) and allowed prefix tuple (`_ALLOWED_PREFIXES`) optimized with precompiled expressions.
- All persistent storage paths must resolve through `src.config` sandboxed filesystem functions.
- Preserve zero-comment and zero-docstring clean code rules inside Python implementations.

## Verification

- Run AST architecture compliance linter:
  ```bash
  human-skills '{"tool_name": "linter", "tool_args": {"scan_path": "src/apps/waf"}}'
  ```
- Run targeted sub-engine and manager test suites:
  ```bash
  PYTHONPATH=. pytest tests/apps/waf/ -v --durations=0
  ```
- Run end-to-end middleware integration test suite:
  ```bash
  PYTHONPATH=. pytest tests/helpers/test_waf_middleware_e2e.py -v --durations=0
  ```
- Related test suites:
  - `tests/apps/waf/test_manager.py`
  - `tests/apps/waf/helpers/test_schema.py`
  - `tests/apps/waf/helpers/test_rule_engine.py`
  - `tests/apps/waf/helpers/test_anomaly.py`
  - `tests/apps/waf/helpers/test_rate_limiter.py`
  - `tests/apps/waf/helpers/test_ip_reputation.py`
  - `tests/apps/waf/helpers/test_traffic_store.py`

## Child DOX Index

- [helpers/schema.py](helpers/schema.py)
- [helpers/rule_engine.py](helpers/rule_engine.py)
- [helpers/anomaly.py](helpers/anomaly.py)
- [helpers/rate_limiter.py](helpers/rate_limiter.py)
- [helpers/ip_reputation.py](helpers/ip_reputation.py)
- [helpers/traffic_store.py](helpers/traffic_store.py)
