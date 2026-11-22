from __future__ import annotations
import asyncio
import time
from typing import Optional
from src.config import Settings, setup_logger, set_telemetry
from src.apps.waf.schema import InspectionResult, ThreatCategory, TrafficEntry, WAFStats
from src.apps.waf.helpers.rule_engine import RuleEngine, _ALLOWED_PREFIXES
from src.apps.waf.helpers.anomaly import AnomalyScorer
from src.apps.waf.helpers.rate_limiter import TokenBucketRateLimiter
from src.apps.waf.helpers.ip_reputation import IPReputationManager
from src.apps.waf.helpers.traffic_store import TrafficStore

logger = setup_logger(Settings.LOG_DIR / "waf.log", name="apps.waf.manager")

_FLUSH_INTERVAL_SECONDS = 30.0

async def _waf_sleep(interval: float) -> None:
    await asyncio.sleep(interval)

class WAFManager:
    _instance: Optional[WAFManager] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> WAFManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        allowed_prefixes: tuple[str, ...] | None = None,
        high_capacity_prefixes: tuple[str, ...] | None = None,
    ) -> None:
        if self._initialized:
            return
        prefixes = allowed_prefixes if allowed_prefixes is not None else _ALLOWED_PREFIXES
        self._rule_engine = RuleEngine(allowed_prefixes=prefixes)
        self._anomaly_scorer = AnomalyScorer(threshold=50.0)
        self._rate_limiter = TokenBucketRateLimiter(high_capacity_prefixes=high_capacity_prefixes)
        self._reputation = IPReputationManager()
        self._traffic_store = TrafficStore()
        self._allowed_prefixes: tuple[str, ...] = prefixes
        self._lock = asyncio.Lock()
        self._bg_task: Optional[asyncio.Task[None]] = None
        self._initialized = True
        logger.info(f"WAFManager initialized with {self._reputation.active_bans_count()} active ban(s)")

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None
        cls._initialized = False

    def is_allowed_path(self, path: str) -> bool:
        return self._rule_engine.is_allowed_path(path)

    def is_banned(self, ip: str) -> bool:
        return self._reputation.is_banned(ip)

    def is_whitelisted(self, ip: str) -> bool:
        return self._reputation.is_whitelisted(ip)

    def start_flush_task(self) -> None:
        if self._bg_task is None or self._bg_task.done():
            self._bg_task = asyncio.create_task(self._periodic_flush())
            logger.info(f"WAFManager background flush task started (interval: {_FLUSH_INTERVAL_SECONDS}s)")

    async def _periodic_flush(self) -> None:
        set_telemetry(service="waf")
        while True:
            await _waf_sleep(_FLUSH_INTERVAL_SECONDS)
            async with self._lock:
                self._reputation.flush()
                self._traffic_store.flush()
                self._reputation.cleanup_expired()
                self._rate_limiter.cleanup_stale()

    async def shutdown(self) -> None:
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError as err:
                logger.debug(f"WAFManager background task cancelled cleanly: {err}")
        async with self._lock:
            self._reputation.flush()
            self._traffic_store.flush()
        logger.info("WAFManager shutdown complete with disk flush")

    async def inspect(
        self,
        ip: str,
        path: str,
        query: str = "",
        headers: dict[str, str] | None = None,
        method: str = "GET",
    ) -> InspectionResult:
        hdrs = headers or {}
        if self.is_whitelisted(ip):
            return InspectionResult(decision="allow", reason="whitelisted")

        if self.is_banned(ip):
            return InspectionResult(
                decision="block",
                reason="ip_banned",
                score=100.0,
                threat_category=ThreatCategory.UNKNOWN,
            )

        rl_decision = self._rate_limiter.check(ip, path)
        if not rl_decision.allowed:
            logger.warning(f"[WAF] Rate limit exceeded by {ip} on {path} (reset: {rl_decision.reset_seconds:.1f}s)")
            self._reputation.record_threat(ip, "rate_limit_exceeded", strikes=1)
            return InspectionResult(
                decision="rate_limit",
                reason="rate_limit_exceeded",
                score=40.0,
                threat_category=ThreatCategory.RATE_LIMIT,
            )

        ua = hdrs.get("user-agent", "")
        combined = f"{method} {path} {query} user-agent:{ua}"
        rule_matches = self._rule_engine.match(combined)

        if rule_matches:
            top_match = max(rule_matches, key=lambda m: m.score)
            critical = top_match.severity == "critical" or top_match.category == ThreatCategory.RCE
            strikes = 3 if (top_match.category in (ThreatCategory.HONEYPOT, ThreatCategory.SCANNER)) else 1
            self._reputation.record_threat(ip, f"rule:{top_match.rule_id}", strikes=strikes, critical=critical)
            return InspectionResult(
                decision="block",
                reason=f"rule:{top_match.rule_id}",
                score=top_match.score,
                threat_category=top_match.category,
                matched_rules=[m.rule_id for m in rule_matches],
            )

        score, indicators, is_anomaly = self._anomaly_scorer.score(method, path, query, hdrs)
        if is_anomaly:
            self._reputation.record_threat(ip, "anomaly_threshold_exceeded", strikes=2)
            return InspectionResult(
                decision="block",
                reason="anomaly_threshold_exceeded",
                score=score,
                threat_category=ThreatCategory.ANOMALY,
                indicators=indicators,
            )

        if not self._rule_engine.is_allowed_path(path):
            self._reputation.record_threat(ip, f"unwhitelisted_path:{path}", strikes=1)
            if self.is_banned(ip):
                return InspectionResult(
                    decision="block",
                    reason="unwhitelisted_path_banned",
                    score=50.0,
                    threat_category=ThreatCategory.UNKNOWN,
                )

        return InspectionResult(decision="allow", reason="ok", score=score, indicators=indicators)

    async def check_request(
        self,
        ip: str,
        path: str,
        query: str = "",
        headers: dict[str, str] | None = None,
        method: str = "GET",
    ) -> bool:
        result = await self.inspect(ip, path, query, headers, method)
        return result.decision == "allow"

    async def track_url(self, path: str, status_code: int) -> None:
        self._traffic_store.track_url(path, status_code)

    def record_traffic(
        self,
        method: str,
        path: str,
        client_ip: str,
        user_agent: str,
        decision: str,
        reason: str,
        score: float,
        threat_category: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        self._traffic_store.record_entry(TrafficEntry(
            timestamp=time.time(),
            method=method,
            path=path,
            client_ip=client_ip,
            user_agent=user_agent,
            decision=decision,
            reason=reason,
            score=score,
            threat_category=threat_category,
            status_code=status_code,
            latency_ms=latency_ms,
        ))

    def get_stats(self) -> WAFStats:
        return self._traffic_store.get_stats(active_bans=self._reputation.active_bans_count())

    def ban_ip(self, ip: str, duration_seconds: float, reason: str) -> None:
        self._reputation.ban(ip, duration_seconds, reason)

    def unban_ip(self, ip: str) -> bool:
        return self._reputation.unban(ip)
