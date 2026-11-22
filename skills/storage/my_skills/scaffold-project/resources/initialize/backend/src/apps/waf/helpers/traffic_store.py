import time
from collections import deque
from src.config import Settings, ensure_dir, exists, read_json, write_json, setup_logger
from src.apps.waf.schema import TrafficEntry, WAFStats, URL_STATUS_DICT_ADAPTER

logger = setup_logger(Settings.LOG_DIR / "waf.log", name="apps.waf.traffic")

class TrafficStore:
    def __init__(self, max_entries: int = 1000, storage_path: str = "data/waf/requested_url.json") -> None:
        self._max_entries = max_entries
        self._storage_path = storage_path
        self._dir_path = storage_path.rsplit("/", 1)[0]
        ensure_dir(self._dir_path)
        self._entries: deque[TrafficEntry] = deque(maxlen=max_entries)
        self._requested_urls: dict[str, int] = {}
        self._dirty: bool = False
        self._start_time: float = time.time()
        self._total_requests: int = 0
        self._total_allowed: int = 0
        self._total_blocked: int = 0
        self._total_rate_limited: int = 0
        self._by_category: dict[str, int] = {}
        self._by_rule: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        if not exists(self._storage_path):
            return
        try:
            raw = read_json(self._storage_path)
            self._requested_urls = URL_STATUS_DICT_ADAPTER.validate_python(raw)
        except Exception as e:
            logger.warning(f"Failed to load requested URLs: {e}")
            self._requested_urls = {}

    def record_entry(self, entry: TrafficEntry) -> None:
        self._entries.append(entry)
        self._total_requests += 1

        if entry.decision == "allow":
            self._total_allowed += 1
        elif entry.decision == "rate_limit":
            self._total_rate_limited += 1
        else:
            self._total_blocked += 1

        if entry.threat_category and entry.threat_category != "unknown":
            self._by_category[entry.threat_category] = self._by_category.get(entry.threat_category, 0) + 1

        if entry.reason.startswith("rule:"):
            rule_id = entry.reason.split(":", 1)[1]
            self._by_rule[rule_id] = self._by_rule.get(rule_id, 0) + 1

    def track_url(self, path: str, status_code: int) -> None:
        if self._requested_urls.get(path) != status_code:
            self._requested_urls[path] = status_code
            self._dirty = True

    def flush(self) -> None:
        if not self._dirty:
            return
        try:
            write_json(self._storage_path, self._requested_urls)
            self._dirty = False
        except Exception as e:
            logger.error(f"Failed to flush requested URLs: {e}")

    def get_stats(self, active_bans: int = 0) -> WAFStats:
        now = time.time()
        uptime = max(0.001, now - self._start_time)
        rpm = (self._total_requests / uptime) * 60.0
        block_rate = (self._total_blocked / self._total_requests * 100.0) if self._total_requests > 0 else 0.0

        return WAFStats(
            total_requests=self._total_requests,
            total_allowed=self._total_allowed,
            total_blocked=self._total_blocked,
            total_rate_limited=self._total_rate_limited,
            active_bans_count=active_bans,
            by_threat_category=dict(self._by_category),
            by_rule=dict(self._by_rule),
            uptime_seconds=uptime,
            requests_per_minute=rpm,
            block_rate_percent=block_rate,
        )

    def get_recent_entries(self, limit: int = 50) -> list[TrafficEntry]:
        return list(self._entries)[-limit:]
