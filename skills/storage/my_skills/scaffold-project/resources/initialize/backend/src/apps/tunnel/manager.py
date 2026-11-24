from __future__ import annotations
import asyncio
import threading
import weakref
from collections import deque
from typing import Optional
from src.config import Settings, ensure_dir, exists, get_mtime, setup_logger, write_json
from src.helpers import get_now_iso
from .helpers import origin_from_url
from .providers import BaseTunnelProvider, create_provider
from .schema import (
    TunnelEvent,
    TunnelEventType,
    TunnelPersistedState,
    TunnelProvider,
    TunnelState,
    TunnelStatus,
    normalize_provider,
)

logger = setup_logger(Settings.LOG_DIR / "tunnel.log", name="apps.tunnel.manager")

STATE_FILE = "data/apps/tunnel/state.json"
_RECONFIG_KEYS: frozenset[str] = frozenset({
    "TUNNEL_PROVIDER",
    "TUNNEL_TARGET_HOST",
    "TUNNEL_TARGET_PORT",
    "TUNNEL_CLOUDFLARE_TOKEN",
    "TUNNEL_CLOUDFLARE_HOSTNAME",
    "TUNNEL_TAILSCALE_AUTHKEY",
    "TUNNEL_TAILSCALE_HTTPS_PORT",
})


class TunnelManager:
    _instance: Optional[TunnelManager] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._state: TunnelState = TunnelState.DISABLED
        self._adapter: Optional[BaseTunnelProvider] = None
        self._active_provider: Optional[TunnelProvider] = None
        self._active_target: Optional[tuple[str, int]] = None
        self._public_url: Optional[str] = None
        self._owned_public_url: Optional[str] = None
        self._last_error: Optional[str] = None
        self._started_at: Optional[str] = None
        self._restart_count: int = 0
        self._events: deque[TunnelEvent] = deque(maxlen=50)
        self._config_mtime: float = 0.0
        self._stop_event: Optional[asyncio.Event] = None
        self._watch_task: Optional[asyncio.Task[None]] = None
        self._thread_lock = threading.Lock()
        self._loop_locks: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = weakref.WeakKeyDictionary()

    @classmethod
    def get_instance(cls) -> TunnelManager:
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

    def _record_event(self, event: TunnelEventType, message: str, url: Optional[str] = None) -> None:
        provider_name = self._active_provider.value if self._active_provider is not None else Settings.TUNNEL_PROVIDER
        self._events.append(
            TunnelEvent(
                event=event,
                message=message,
                timestamp=get_now_iso(),
                url=url,
                provider=provider_name,
            )
        )

    def _safe_provider(self) -> TunnelProvider:
        try:
            return normalize_provider(Settings.TUNNEL_PROVIDER)
        except Exception:
            return TunnelProvider.CLOUDFLARED

    def _persist_state(self) -> None:
        try:
            ensure_dir("data/apps/tunnel")
            payload = TunnelPersistedState(
                provider=self._active_provider or self._safe_provider(),
                target_host=Settings.TUNNEL_TARGET_HOST,
                target_port=Settings.resolved_tunnel_port,
                public_url=self._public_url,
                state=self._state,
                updated_at=get_now_iso(),
            )
            write_json(STATE_FILE, payload.model_dump(mode="json"))
        except Exception as err:
            logger.debug(f"tunnel.manager.state_persist_err err={err}")

    def _sync_config_mtime(self) -> None:
        cfg_path = Settings.TUNNEL_CONFIG_FILE
        if exists(cfg_path):
            try:
                self._config_mtime = get_mtime(cfg_path)
            except OSError as err:
                logger.debug(f"tunnel.manager.mtime_err path={cfg_path} err={err}")

    def _reload_config_if_changed(self) -> dict[str, tuple[float | int | str | bool, float | int | str | bool]]:
        cfg_path = Settings.TUNNEL_CONFIG_FILE
        if not exists(cfg_path):
            return {}
        try:
            mtime = get_mtime(cfg_path)
        except OSError:
            return {}
        if mtime <= self._config_mtime:
            return {}
        self._config_mtime = mtime
        try:
            changes = Settings.reload_tunnel_env()
            if changes:
                keys = ",".join(sorted(changes.keys()))
                logger.info(f"tunnel.config.reloaded path={cfg_path} updated={keys}")
            return changes
        except Exception as err:
            logger.error(f"tunnel.config.reload_failed path={cfg_path} err={err}")
            return {}

    async def activate_async(self, provider: Optional[str] = None, port: Optional[int] = None) -> Optional[str]:
        lock = self._get_op_lock()
        async with lock:
            return await self._activate_unlocked(provider=provider, port=port)

    async def _activate_unlocked(self, provider: Optional[str] = None, port: Optional[int] = None) -> Optional[str]:
        target_port = port if (port is not None and port > 0) else Settings.resolved_tunnel_port
        target_host = Settings.TUNNEL_TARGET_HOST.strip() or "127.0.0.1"
        try:
            resolved_provider = normalize_provider(provider if provider is not None else Settings.TUNNEL_PROVIDER)
        except Exception as err:
            self._last_error = str(err)
            self._state = TunnelState.ERROR
            self._record_event(TunnelEventType.ERROR, self._last_error)
            self._persist_state()
            logger.error(f"tunnel.manager.invalid_provider err={err}")
            return None

        if (
            self._state == TunnelState.ACTIVE
            and self._adapter is not None
            and self._adapter.is_alive()
            and self._active_provider == resolved_provider
            and self._active_target == (target_host, target_port)
            and self._public_url
        ):
            return self._public_url

        if self._adapter is not None:
            await self._deactivate_unlocked(target_state=TunnelState.STARTING)

        self._state = TunnelState.STARTING
        self._active_provider = resolved_provider
        self._active_target = (target_host, target_port)
        self._last_error = None
        adapter = create_provider(
            provider=resolved_provider,
            target_host=target_host,
            target_port=target_port,
            timeout=Settings.TUNNEL_START_TIMEOUT_SEC,
            notify=self._record_event,
        )
        try:
            url = await asyncio.to_thread(adapter.start)
        except Exception as err:
            self._last_error = str(err)
            self._state = TunnelState.ERROR
            self._adapter = None
            self._public_url = None
            self._record_event(TunnelEventType.ERROR, self._last_error)
            self._persist_state()
            logger.error(f"tunnel.manager.start_failed provider={resolved_provider.value} err={err}")
            return None

        self._adapter = adapter
        self._public_url = url
        self._owned_public_url = url
        self._started_at = get_now_iso()
        self._state = TunnelState.ACTIVE
        self._restart_count = 0
        Settings.PUBLIC_URL = url
        self._persist_state()
        logger.info(f"tunnel.manager.active provider={resolved_provider.value} target={target_host}:{target_port} url={url}")
        return url

    async def deactivate_async(self) -> bool:
        lock = self._get_op_lock()
        async with lock:
            target = TunnelState.STANDBY if Settings.TUNNEL_MANAGER else TunnelState.DISABLED
            return await self._deactivate_unlocked(target_state=target)

    async def _deactivate_unlocked(self, target_state: TunnelState) -> bool:
        adapter = self._adapter
        self._state = TunnelState.STOPPING
        stopped = True
        if adapter is not None:
            try:
                stopped = await asyncio.to_thread(adapter.stop)
            except Exception as err:
                stopped = False
                logger.warning(f"tunnel.manager.stop_err err={err}")
        self._adapter = None
        if self._owned_public_url and Settings.PUBLIC_URL == self._owned_public_url:
            Settings.PUBLIC_URL = None
        self._owned_public_url = None
        self._public_url = None
        self._started_at = None
        self._state = target_state
        self._persist_state()
        return stopped

    async def _apply_hot_reload(self, changes: dict[str, tuple[float | int | str | bool, float | int | str | bool]]) -> bool:
        if not Settings.TUNNEL_MANAGER:
            logger.info("tunnel.manager.disabled_via_hot_reload")
            await self.deactivate_async()
            self._state = TunnelState.DISABLED
            self._persist_state()
            return False
        if not Settings.TUNNEL:
            if self._adapter is not None or self._state != TunnelState.STANDBY:
                logger.info("tunnel.manager.deactivating_via_hot_reload")
                await self.deactivate_async()
            return True
        needs_restart = bool(_RECONFIG_KEYS.intersection(changes.keys()))
        if needs_restart and self._adapter is not None:
            logger.info("tunnel.manager.restarting_on_config_change")
            await self.deactivate_async()
            await self.activate_async()
            return True
        if self._state in {TunnelState.STANDBY, TunnelState.DISABLED, TunnelState.ERROR}:
            logger.info("tunnel.manager.activating_via_hot_reload")
            await self.activate_async()
        return True

    def _compute_backoff_sec(self) -> float:
        return min(30.0, float(2 ** min(self._restart_count, 4)))

    async def _run_watchdog_tick(self) -> None:
        if not Settings.TUNNEL or self._state != TunnelState.ACTIVE:
            return
        if self._adapter is not None and self._adapter.is_alive():
            return
        if not Settings.TUNNEL_AUTO_RESTART or self._restart_count >= Settings.TUNNEL_MAX_RESTARTS:
            self._last_error = "Tunnel process exited and auto-restart limit reached"
            self._state = TunnelState.ERROR
            self._record_event(TunnelEventType.ERROR, self._last_error)
            self._persist_state()
            logger.error(f"tunnel.manager.watchdog_exhausted restarts={self._restart_count}")
            return
        self._restart_count += 1
        self._state = TunnelState.RECONNECTING
        backoff = self._compute_backoff_sec()
        logger.warning(f"tunnel.manager.reconnecting attempt={self._restart_count}/{Settings.TUNNEL_MAX_RESTARTS} backoff={backoff:.1f}s")
        await self.deactivate_async()
        if backoff > 0.0 and self._stop_event is not None:
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=backoff)
                return
            except asyncio.TimeoutError:
                logger.debug(f"tunnel.manager.backoff_elapsed attempt={self._restart_count}")
        if Settings.TUNNEL_MANAGER and Settings.TUNNEL:
            await self.activate_async()

    async def poll_once_async(self) -> bool:
        changes = self._reload_config_if_changed()
        if changes:
            keep_running = await self._apply_hot_reload(changes)
            if not keep_running:
                return False
        await self._run_watchdog_tick()
        return True

    async def _supervisor_loop(self) -> None:
        stop_event = self._stop_event
        if stop_event is None:
            return
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=Settings.TUNNEL_POLL_INTERVAL_SEC)
                break
            except asyncio.TimeoutError:
                logger.debug("tunnel.manager.supervisor_tick")
            keep_running = await self.poll_once_async()
            if not keep_running:
                break

    async def start_async(self) -> Optional[str]:
        self._sync_config_mtime()
        if not Settings.TUNNEL_MANAGER:
            self._state = TunnelState.DISABLED
            logger.info("TunnelManager disabled (TUNNEL_MANAGER=false)")
            return None
        if self._watch_task is None or self._watch_task.done():
            self._stop_event = asyncio.Event()
            self._watch_task = asyncio.create_task(self._supervisor_loop(), name="tunnel-manager-supervisor")
        if not Settings.TUNNEL:
            self._state = TunnelState.STANDBY
            self._persist_state()
            logger.info("TunnelManager running in standby (TUNNEL=false); watching env/.1t2u3n4n5e6l7")
            return None
        return await self.activate_async()

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
                logger.debug("TunnelManager supervisor task cancelled on shutdown")
        await self.deactivate_async()
        self._state = TunnelState.DISABLED
        self._persist_state()
        logger.info("TunnelManager stopped cleanly")

    def get_tunnel_url(self) -> Optional[str]:
        if self._state == TunnelState.ACTIVE and self._adapter is not None and self._adapter.is_alive():
            return self._public_url
        return None

    def get_active_origin(self) -> Optional[str]:
        url = self.get_tunnel_url()
        return origin_from_url(url) if url else None

    def get_events(self, clear: bool = False) -> list[TunnelEvent]:
        items = list(self._events)
        if clear:
            self._events.clear()
        return items

    def get_status(self) -> TunnelStatus:
        active_url = self.get_tunnel_url()
        return TunnelStatus(
            manager_enabled=Settings.TUNNEL_MANAGER,
            tunnel_enabled=Settings.TUNNEL,
            state=self._state,
            provider=self._active_provider or self._safe_provider(),
            target_host=Settings.TUNNEL_TARGET_HOST,
            target_port=Settings.resolved_tunnel_port,
            public_url=active_url,
            origin=origin_from_url(active_url) if active_url else None,
            restart_count=self._restart_count,
            last_error=self._last_error,
            started_at=self._started_at,
            updated_at=get_now_iso(),
        )


def get_tunnel_manager() -> TunnelManager:
    return TunnelManager.get_instance()
