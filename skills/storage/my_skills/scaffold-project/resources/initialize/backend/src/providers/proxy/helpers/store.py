from __future__ import annotations
from typing import Optional
from src.config import Settings, ensure_dir, exists, read_json, setup_logger, write_json
from src.helpers import get_now_iso
from ..schema import (
    PROXY_CACHE_ADAPTER,
    PROXY_STATE_ADAPTER,
    ProxyCacheFile,
    ProxyPersistedState,
    ProxyProviderType,
    ProxyState,
)

logger = setup_logger(Settings.LOG_DIR / "proxy.log", name="providers.proxy.store")


class ProxyStore:
    @staticmethod
    def _ensure_parent(rel_path: str) -> None:
        if "/" in rel_path:
            ensure_dir(rel_path.rsplit("/", 1)[0])

    @classmethod
    def load_cache(cls, cache_path: str) -> ProxyCacheFile:
        if not exists(cache_path):
            return ProxyCacheFile()
        try:
            return PROXY_CACHE_ADAPTER.validate_python(read_json(cache_path))
        except Exception as err:
            logger.warning(f"proxy.store.cache_load_failed path={cache_path} err={err}")
            return ProxyCacheFile()

    @classmethod
    def save_cache(cls, cache_path: str, proxies: list[str], provider: ProxyProviderType) -> bool:
        try:
            cls._ensure_parent(cache_path)
            payload = ProxyCacheFile(
                proxies=proxies,
                count=len(proxies),
                provider=provider,
                updated_at=get_now_iso(),
            )
            write_json(cache_path, payload.model_dump(mode="json"))
            return True
        except Exception as err:
            logger.error(f"proxy.store.cache_save_failed path={cache_path} err={err}")
            return False

    @classmethod
    def load_state(cls, state_path: str) -> Optional[ProxyPersistedState]:
        if not exists(state_path):
            return None
        try:
            return PROXY_STATE_ADAPTER.validate_python(read_json(state_path))
        except Exception as err:
            logger.warning(f"proxy.store.state_load_failed path={state_path} err={err}")
            return None

    @classmethod
    def save_state(
        cls,
        state_path: str,
        state: ProxyState,
        provider: ProxyProviderType,
        total_proxies: int,
        last_refresh_at: Optional[str],
        last_error: Optional[str],
    ) -> None:
        try:
            cls._ensure_parent(state_path)
            payload = ProxyPersistedState(
                state=state,
                provider=provider,
                last_refresh_at=last_refresh_at,
                total_proxies=total_proxies,
                last_error=last_error,
                updated_at=get_now_iso(),
            )
            write_json(state_path, payload.model_dump(mode="json"))
        except Exception as err:
            logger.debug(f"proxy.store.state_save_failed path={state_path} err={err}")
