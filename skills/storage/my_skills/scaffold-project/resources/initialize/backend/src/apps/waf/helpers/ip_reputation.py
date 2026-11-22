import ipaddress
import time
from src.config import Settings, ensure_dir, exists, read_json, write_json, setup_logger
from src.apps.waf.schema import BanRecord, BAN_RECORD_DICT_ADAPTER

logger = setup_logger(Settings.LOG_DIR / "waf.log", name="apps.waf.reputation")

_LOOPBACK_IPS: frozenset[str] = frozenset({"127.0.0.1", "::1", "localhost"})

_TRUSTED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
)

class IPReputationManager:
    def __init__(self, storage_path: str = "data/waf/blacklist.json") -> None:
        self._storage_path = storage_path
        self._dir_path = storage_path.rsplit("/", 1)[0]
        ensure_dir(self._dir_path)
        self._records: dict[str, BanRecord] = {}
        self._active_bans: set[str] = set()
        self._dirty: bool = False
        self._load()

    def _load(self) -> None:
        if not exists(self._storage_path):
            return
        try:
            raw = read_json(self._storage_path)
            for k, v in raw.items():
                if not v.get("ip"):
                    v["ip"] = k
            self._records = BAN_RECORD_DICT_ADAPTER.validate_python(raw)
            now = time.time()
            self._active_bans = {
                ip for ip, rec in self._records.items()
                if rec.banned_until > now and not self.is_whitelisted(ip)
            }
        except Exception as e:
            logger.warning(f"Failed to load blacklist from {self._storage_path}: {e}")
            self._records = {}
            self._active_bans = set()

    def is_whitelisted(self, ip: str) -> bool:
        if ip in _LOOPBACK_IPS or not ip or ip == "unknown":
            return True
        try:
            addr = ipaddress.ip_address(ip)
            for net in _TRUSTED_NETWORKS:
                if addr in net:
                    return True
        except ValueError:
            return False
        return False

    def is_banned(self, ip: str) -> bool:
        if self.is_whitelisted(ip):
            return False
        return ip in self._active_bans

    def record_threat(self, ip: str, reason: str, strikes: int = 1, critical: bool = False) -> bool:
        if self.is_whitelisted(ip):
            return False

        now = time.time()
        record = self._records.get(ip)
        if record is None:
            record = BanRecord(ip=ip, strikes=0, banned_until=0.0, reason=reason, created_at=now)
            self._records[ip] = record

        record.strikes += strikes
        record.reason = reason
        self._dirty = True

        if critical:
            record.banned_until = now + 86400.0
            self._active_bans.add(ip)
            logger.warning(f"[WAF] Critical threat by {ip}: {reason} -> BANNED 24h")
            return True

        if record.strikes >= 6 or (record.strikes >= 3 and record.banned_until > 0 and now > record.banned_until):
            record.banned_until = now + 86400.0
            self._active_bans.add(ip)
            logger.warning(f"[WAF] Repeated violations by {ip}: {reason} -> BANNED 24h")
            return True

        if record.strikes >= 3:
            record.banned_until = now + 3600.0
            self._active_bans.add(ip)
            logger.warning(f"[WAF] Strike threshold hit by {ip}: {reason} -> BANNED 1h")
            return True

        return False

    def ban(self, ip: str, duration_seconds: float, reason: str) -> None:
        if self.is_whitelisted(ip):
            return
        now = time.time()
        record = self._records.get(ip)
        if record is None:
            record = BanRecord(ip=ip, strikes=3, banned_until=now + duration_seconds, reason=reason, created_at=now)
            self._records[ip] = record
        else:
            record.banned_until = max(record.banned_until, now + duration_seconds)
            record.reason = reason
        self._active_bans.add(ip)
        self._dirty = True

    def unban(self, ip: str) -> bool:
        removed = False
        if ip in self._active_bans:
            self._active_bans.remove(ip)
            removed = True
        record = self._records.get(ip)
        if record is not None:
            record.banned_until = 0.0
            record.strikes = 0
            self._dirty = True
            removed = True
        return removed

    def flush(self) -> None:
        if not self._dirty:
            return
        try:
            dumped = {ip: rec.model_dump() for ip, rec in self._records.items()}
            write_json(self._storage_path, dumped)
            self._dirty = False
        except Exception as e:
            logger.error(f"Failed to flush blacklist: {e}")

    def cleanup_expired(self) -> tuple[int, int]:
        now = time.time()
        expired = {ip for ip in self._active_bans if self._records.get(ip) and self._records[ip].banned_until <= now}
        if expired:
            self._active_bans -= expired

        cutoff = now - (7.0 * 86400.0)
        stale = [
            ip for ip, rec in self._records.items()
            if rec.banned_until < cutoff and ip not in self._active_bans
        ]
        for ip in stale:
            del self._records[ip]

        if expired or stale:
            self._dirty = True
        return len(expired), len(stale)

    def active_bans_count(self) -> int:
        return len(self._active_bans)
