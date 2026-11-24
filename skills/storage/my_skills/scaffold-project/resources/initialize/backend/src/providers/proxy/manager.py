from __future__ import annotations
import asyncio
import threading
import time
import weakref
from typing import Optional
from src.config import EnvChanges, Settings, get_env_reloader, setup_logger
from src.helpers import get_now_iso, get_now_utc, parse_iso, sanitize_proxy_url
from .helpers import ProxyFetcher, ProxyStore
from .schema import ProxyProviderType, ProxyState, ProxyStatus, normalize_proxy_provider

logger = setup_logger(Settings.LOG_DIR / "proxy.log", name="providers.proxy.manager")

_REFRESH_TRIGGER_KEYS: frozenset[str] = frozenset({
    "PROXY_PROVIDER",
    "PROXY_STATIC_URLS",
    "WEBSHARE_API_URL",
    "WEBSHARE_TOKEN",
    "PROXY_CACHE_PATH",
})


class ProxyManager:
    _instance: Optional[ProxyManager] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._state: ProxyState = ProxyState.DISABLED
        self._proxies: list[str] = []
        self._cursor: int = 0
        self._failures: dict[str, int] = {}
        self._cooldown_until: dict[str, float] = {}
        self._last_refresh_at: Optional[str] = None
        self._last_error: Optional[str] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._watch_task: Optional[asyncio.Task[None]] = None
        self._thread_lock = threading.Lock()
        self._loop_locks: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = weakref.WeakKeyDictionary()
        get_env_reloader().register(
            name="proxy",
            env_path_fn=lambda: Settings.PROXY_CONFIG_FILE,
            prefixes=("PROXY_", "WEBSHARE_"),
            exact_keys=("PROXY",),
            on_change=self._on_env_changed,
        )

    @classmethod
    def get_instance(cls) -> ProxyManager:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            cls._instance = None

    def _get_op_lock(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        with self._thread_lock:
            lock = self._loop_locks.get(loop)
            if lock is None:
                lock = asyncio.Lock()
                self._loop_locks[loop] = lock
            return lock

    def _safe_provider(self) -> ProxyProviderType:
        try:
            return normalize_proxy_provider(Settings.PROXY_PROVIDER)
        except Exception:
            return ProxyProviderType.WEBSHARE

    def _persist_state(self) -> None:
        ProxyStore.save_state(
            state_path=Settings.PROXY_STATE_PATH,
            state=self._state,
            provider=self._safe_provider(),
            total_proxies=len(self._proxies),
            last_refresh_at=self._last_refresh_at,
            last_error=self._last_error,
        )

    def _sync_config_state(self) -> None:
        get_env_reloader().sync_entry("proxy")

    async def _on_env_changed(self, changes: EnvChanges) -> None:
        if not Settings.PROXY_MANAGER:
            logger.info("proxy.manager.disabled_via_hot_reload")
            await self.deactivate_async()
            self._state = ProxyState.DISABLED
            self._persist_state()
            return
        if not Settings.PROXY:
            logger.info("proxy.manager.deactivating_via_hot_reload")
            await self.deactivate_async()
            return
        force_refresh = bool(_REFRESH_TRIGGER_KEYS.intersection(changes.keys()))
        if force_refresh or self._state in {ProxyState.STANDBY, ProxyState.DISABLED, ProxyState.ERROR}:
            logger.info(f"proxy.manager.activating_via_hot_reload force_refresh={force_refresh}")
            await self.activate_async(force_refresh=force_refresh)

    async def _check_config_reload(self) -> list[str]:
        changes = await get_env_reloader().check_entry_async("proxy")
        return sorted(changes.keys())

    def _needs_refresh(self) -> bool:
        if not self._proxies:
            return True
        if not self._last_refresh_at:
            return True
        try:
            elapsed = (get_now_utc() - parse_iso(self._last_refresh_at)).total_seconds()
            return elapsed >= Settings.PROXY_REFRESH_INTERVAL_SEC
        except Exception:
            return True

    def _load_from_cache(self) -> None:
        cached = ProxyStore.load_cache(Settings.PROXY_CACHE_PATH)
        if not cached.proxies:
            return
        with self._thread_lock:
            self._proxies = list(cached.proxies)
            self._cursor = 0
        self._last_refresh_at = cached.updated_at

    def _healthy_count_locked(self, now_mono: float) -> tuple[int, int]:
        cooldown = 0
        for url in self._proxies:
            if self._cooldown_until.get(url, 0.0) > now_mono:
                cooldown += 1
        return len(self._proxies) - cooldown, cooldown

    def _update_active_state(self) -> None:
        now_mono = time.monotonic()
        with self._thread_lock:
            total = len(self._proxies)
            healthy, _ = self._healthy_count_locked(now_mono)
        if total == 0:
            self._state = ProxyState.ERROR
        elif healthy == 0:
            self._state = ProxyState.DEGRADED
        else:
            self._state = ProxyState.ACTIVE

    async def refresh_async(self, force: bool = False) -> bool:
        lock = self._get_op_lock()
        async with lock:
            return await self._refresh_unlocked(force=force)

    async def _refresh_unlocked(self, force: bool = False) -> bool:
        if not force and not self._needs_refresh():
            return True
        try:
            provider = normalize_proxy_provider(Settings.PROXY_PROVIDER)
            fetched = await ProxyFetcher.fetch(provider)
        except Exception as err:
            self._last_error = str(err)
            self._update_active_state()
            self._persist_state()
            logger.error(f"proxy.manager.refresh_failed err={err}")
            return False
        if not fetched:
            self._last_error = "No proxies returned by configured provider"
            self._update_active_state()
            self._persist_state()
            logger.warning("proxy.manager.refresh_empty")
            return False
        ProxyStore.save_cache(Settings.PROXY_CACHE_PATH, fetched, provider)
        with self._thread_lock:
            self._proxies = list(fetched)
            self._cursor = 0
            self._failures.clear()
            self._cooldown_until.clear()
        self._last_refresh_at = get_now_iso()
        self._last_error = None
        self._update_active_state()
        self._persist_state()
        logger.info(f"proxy.manager.refreshed provider={provider.value} count={len(fetched)}")
        return True

    async def activate_async(self, force_refresh: bool = False) -> bool:
        lock = self._get_op_lock()
        async with lock:
            if not force_refresh and not self._proxies:
                self._load_from_cache()
            ok = await self._refresh_unlocked(force=force_refresh)
            if self._proxies:
                self._update_active_state()
                self._persist_state()
                return True
            return ok

    async def deactivate_async(self) -> None:
        lock = self._get_op_lock()
        async with lock:
            with self._thread_lock:
                self._proxies.clear()
                self._cursor = 0
                self._failures.clear()
                self._cooldown_until.clear()
            self._state = ProxyState.STANDBY if Settings.PROXY_MANAGER else ProxyState.DISABLED
            self._persist_state()

    async def poll_once_async(self) -> bool:
        await self._check_config_reload()
        if not Settings.PROXY_MANAGER:
            return False
        if Settings.PROXY and self._needs_refresh():
            await self.refresh_async(force=False)
        return True

    async def _supervisor_loop(self) -> None:
        stop_event = self._stop_event
        if stop_event is None:
            return
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=Settings.PROXY_POLL_INTERVAL_SEC)
                break
            except asyncio.TimeoutError:
                logger.debug("proxy.manager.supervisor_tick")
            keep_running = await self.poll_once_async()
            if not keep_running:
                break

    async def start_async(self) -> bool:
        self._sync_config_state()
        if not Settings.PROXY_MANAGER:
            self._state = ProxyState.DISABLED
            logger.info("ProxyManager disabled (PROXY_MANAGER=false)")
            return False
        if self._watch_task is None or self._watch_task.done():
            self._stop_event = asyncio.Event()
            self._watch_task = asyncio.create_task(self._supervisor_loop(), name="proxy-manager-supervisor")
        if not Settings.PROXY:
            self._state = ProxyState.STANDBY
            self._persist_state()
            logger.info("ProxyManager running in standby (PROXY=false); watching env/.1p2r3o4x5y6")
            return True
        return await self.activate_async(force_refresh=False)

    async def stop_async(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        task = self._watch_task
        self._watch_task = None
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug("ProxyManager supervisor task cancelled on shutdown")
        await self.deactivate_async()
        self._state = ProxyState.DISABLED
        self._persist_state()
        logger.info("ProxyManager stopped cleanly")

    def get_proxies(self) -> list[str]:
        if not Settings.PROXY_MANAGER or not Settings.PROXY:
            return []
        with self._thread_lock:
            return list(self._proxies)

    def get_proxy(self) -> Optional[str]:
        if not Settings.PROXY_MANAGER or not Settings.PROXY:
            return None
        now_mono = time.monotonic()
        with self._thread_lock:
            total = len(self._proxies)
            if total == 0:
                return None
            for _ in range(total):
                candidate = self._proxies[self._cursor % total]
                self._cursor = (self._cursor + 1) % total
                if self._cooldown_until.get(candidate, 0.0) <= now_mono:
                    return candidate
            return None

    def report_success(self, proxy_url: str) -> None:
        with self._thread_lock:
            self._failures.pop(proxy_url, None)
            self._cooldown_until.pop(proxy_url, None)
        if Settings.PROXY_MANAGER and Settings.PROXY:
            self._update_active_state()

    def report_failure(self, proxy_url: str) -> None:
        now_mono = time.monotonic()
        with self._thread_lock:
            count = self._failures.get(proxy_url, 0) + 1
            self._failures[proxy_url] = count
            if count >= Settings.PROXY_MAX_FAILURES:
                self._cooldown_until[proxy_url] = now_mono + Settings.PROXY_COOLDOWN_SEC
                self._failures[proxy_url] = 0
                logger.warning(
                    f"proxy.manager.cooldown proxy={sanitize_proxy_url(proxy_url)} "
                    f"duration={Settings.PROXY_COOLDOWN_SEC:.0f}s"
                )
        if Settings.PROXY_MANAGER and Settings.PROXY:
            self._update_active_state()

    def get_status(self) -> ProxyStatus:
        now_mono = time.monotonic()
        with self._thread_lock:
            total = len(self._proxies)
            healthy, cooldown = self._healthy_count_locked(now_mono)
        return ProxyStatus(
            manager_enabled=Settings.PROXY_MANAGER,
            proxy_enabled=Settings.PROXY,
            state=self._state,
            provider=self._safe_provider(),
            total_proxies=total,
            healthy_proxies=healthy,
            cooldown_proxies=cooldown,
            last_refresh_at=self._last_refresh_at,
            last_error=self._last_error,
            updated_at=get_now_iso(),
        )


def get_proxy_manager() -> ProxyManager:
    return ProxyManager.get_instance()
