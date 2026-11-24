from __future__ import annotations
import hashlib
import inspect
import os
import threading
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional
from .dotenv import parse_env_dict
from .files import exists, get_mtime, read_bytes
from .logger import setup_logger
from .settings import Settings

SettingScalar = float | int | str | bool
EnvChanges = dict[str, tuple[SettingScalar, SettingScalar]]
ReloadCallback = Callable[[EnvChanges], None | Awaitable[None]]

logger = setup_logger(Settings.LOG_DIR / "config.log", name="config.reloader")


def _file_signature(env_path: str) -> Optional[tuple[float, str]]:
    if not exists(env_path):
        return None
    try:
        mtime = get_mtime(env_path)
        digest = hashlib.sha256(read_bytes(env_path)).hexdigest()
        return mtime, digest
    except OSError:
        return None


def reload_env_namespace(
    env_path: str,
    prefixes: tuple[str, ...] = (),
    exact_keys: tuple[str, ...] = (),
) -> EnvChanges:
    parsed = parse_env_dict(env_path)
    if not parsed:
        return {}
    exact_set = set(exact_keys)
    allow_all = not prefixes and not exact_set
    updates = {
        k: v for k, v in parsed.items()
        if (allow_all or k in exact_set or any(k.startswith(p) for p in prefixes))
        and k in type(Settings).model_fields
    }
    if not updates:
        return {}
    candidate_data = Settings.model_dump()
    candidate_data.update(updates)
    candidate = type(Settings).model_validate(candidate_data)
    changes: EnvChanges = {}
    candidate_dict = candidate.model_dump()
    for k in updates:
        old_val = Settings.__dict__.get(k)
        new_val = candidate_dict.get(k)
        if old_val != new_val and old_val is not None and new_val is not None:
            Settings.__dict__[k] = new_val
            Settings.__pydantic_fields_set__.add(k)
            os.environ[k] = updates[k]
            changes[k] = (old_val, new_val)
    return changes


@dataclass
class EnvWatchEntry:
    name: str
    env_path_fn: Callable[[], str]
    prefixes: tuple[str, ...]
    exact_keys: tuple[str, ...]
    on_change: Optional[ReloadCallback] = None
    last_signature: Optional[tuple[float, str]] = None


class EnvHotReloader:
    _instance: Optional[EnvHotReloader] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._entries: dict[str, EnvWatchEntry] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> EnvHotReloader:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            cls._instance = None

    def register(
        self,
        name: str,
        env_path_fn: Callable[[], str],
        prefixes: tuple[str, ...] = (),
        exact_keys: tuple[str, ...] = (),
        on_change: Optional[ReloadCallback] = None,
    ) -> None:
        sig = _file_signature(env_path_fn())
        with self._lock:
            self._entries[name] = EnvWatchEntry(
                name=name,
                env_path_fn=env_path_fn,
                prefixes=prefixes,
                exact_keys=exact_keys,
                on_change=on_change,
                last_signature=sig,
            )

    def unregister(self, name: str) -> None:
        with self._lock:
            self._entries.pop(name, None)

    def sync_entry(self, name: str) -> None:
        with self._lock:
            entry = self._entries.get(name)
        if entry is None:
            return
        sig = _file_signature(entry.env_path_fn())
        with self._lock:
            entry.last_signature = sig

    def _poll_entry(self, entry: EnvWatchEntry) -> tuple[EnvChanges, Optional[ReloadCallback]]:
        cfg_path = entry.env_path_fn()
        sig = _file_signature(cfg_path)
        if sig is None:
            entry.last_signature = None
            return {}, None
        if entry.last_signature is not None and sig == entry.last_signature:
            return {}, None
        entry.last_signature = sig
        try:
            changes = reload_env_namespace(cfg_path, prefixes=entry.prefixes, exact_keys=entry.exact_keys)
            if changes:
                keys = ",".join(sorted(changes.keys()))
                logger.info(f"config.reloaded name={entry.name} path={cfg_path} updated={keys}")
            return changes, entry.on_change
        except Exception as err:
            logger.error(f"config.reload_failed name={entry.name} path={cfg_path} error={err}")
            return {}, None

    def check_entry_sync(self, name: str) -> EnvChanges:
        with self._lock:
            entry = self._entries.get(name)
            if entry is None:
                return {}
            changes, callback = self._poll_entry(entry)
        if changes and callback is not None:
            result = callback(changes)
            if inspect.isawaitable(result):
                logger.warning(f"config.reloader.async_callback_ignored_in_sync name={name}")
        return changes

    async def check_entry_async(self, name: str) -> EnvChanges:
        with self._lock:
            entry = self._entries.get(name)
            if entry is None:
                return {}
            changes, callback = self._poll_entry(entry)
        if changes and callback is not None:
            result = callback(changes)
            if inspect.isawaitable(result):
                await result
        return changes

    async def check_all_async(self) -> dict[str, EnvChanges]:
        with self._lock:
            names = list(self._entries.keys())
        results: dict[str, EnvChanges] = {}
        for name in names:
            changes = await self.check_entry_async(name)
            if changes:
                results[name] = changes
        return results


def get_env_reloader() -> EnvHotReloader:
    return EnvHotReloader.get_instance()
