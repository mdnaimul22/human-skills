from __future__ import annotations

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_NOISY_LOGGERS: tuple[str, ...] = (
    "httpx",
    "openai",
    "anthropic",
    "httpcore",
    "urllib3",
    "asyncio",
    "multipart",
)

_lock = threading.Lock()
_registry: dict[str, logging.Logger] = {}
_file_handlers: dict[str, RotatingFileHandler] = {}
_system_configured = False


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)-35s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _configure_system(log_dir: Path, is_production: bool) -> None:
    global _system_configured
    if _system_configured:
        return

    root = logging.getLogger()
    root.setLevel(logging.INFO if is_production else logging.DEBUG)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    log_dir.mkdir(parents=True, exist_ok=True)
    _system_configured = True


def _safe_symlink(target_name: str, link_path: Path) -> None:
    try:
        if link_path.is_symlink() or link_path.exists():
            return
        link_path.symlink_to(target_name)
    except OSError:
        pass


def _resolve_target(spec: str, root_log_dir: Path, default_base: str = "main.txt") -> tuple[Path, str, str, str]:
    raw = spec.strip()
    if raw.endswith(".txt") or raw.endswith(".log"):
        ext = raw[raw.rfind(".") :]
        stem = raw[: raw.rfind(".")]
    else:
        ext = ".txt"
        stem = raw
        raw = f"{stem}{ext}"

    mod_stem = stem
    for prefix in ("app.", "src.", "myproject."):
        if mod_stem.startswith(prefix):
            mod_stem = mod_stem[len(prefix) :]
            break

    if mod_stem.startswith("agent."):
        mod_stem = f"core.agents.{mod_stem[6:]}"

    parts = [p for p in mod_stem.split(".") if p]
    if len(parts) <= 1:
        dir_path = root_log_dir
        file_name = default_base if not parts else f"{parts[0]}{ext}"
        short_alias = file_name
        return dir_path, file_name, short_alias, stem

    dir_parts = parts[:-1]
    dir_path = root_log_dir
    for dp in dir_parts:
        dir_path = dir_path / dp

    full_filename = f"{'.'.join(dir_parts)}.{parts[-1]}{ext}"
    short_alias = f"{parts[-1]}{ext}"
    return dir_path, full_filename, short_alias, stem


def _get_or_create_handler(
    file_path: Path,
    is_prod: bool,
    formatter: logging.Formatter,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> RotatingFileHandler:
    key = str(file_path.resolve())
    if key in _file_handlers:
        return _file_handlers[key]

    file_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO if is_prod else logging.DEBUG)
    handler.setFormatter(formatter)
    _file_handlers[key] = handler
    return handler


def setup_logger(
    boss_name: str,
    his_name: str | None = None,
    **kwargs,
) -> logging.Logger:
    if "name" in kwargs and his_name is None:
        his_name = str(kwargs["name"])

    if isinstance(boss_name, Path):
        boss_name = str(boss_name)

    if his_name is None and ("/" in boss_name or "\\" in boss_name):
        p = Path(boss_name)
        boss_name = "main.txt"
        his_name = p.name

    if his_name is None:
        his_name = boss_name

    with _lock:
        from .settings import Settings

        is_prod: bool = Settings.is_production
        log_dir: Path = Settings.LOG_DIR

        _configure_system(log_dir, is_prod)

        boss_dir, boss_full, boss_alias, boss_stem = _resolve_target(boss_name, log_dir, default_base="main.txt")

        logger_key = boss_stem if his_name is None else _resolve_target(his_name, log_dir)[3]
        if logger_key in _registry:
            return _registry[logger_key]

        logger = logging.getLogger(logger_key)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if logger.handlers:
            _registry[logger_key] = logger
            return logger

        fmt = _build_formatter()

        boss_path = boss_dir / "main.txt"
        boss_handler = _get_or_create_handler(boss_path, is_prod, fmt)
        logger.addHandler(boss_handler)

        if his_name is not None:
            his_dir, his_full, his_alias, _ = _resolve_target(his_name, log_dir, default_base="main.txt")
            his_path = his_dir / his_full
            if his_path.resolve() != boss_path.resolve():
                his_handler = _get_or_create_handler(his_path, is_prod, fmt)
                logger.addHandler(his_handler)
            if his_full != his_alias:
                _safe_symlink(his_full, his_dir / his_alias)

        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.WARNING if is_prod else logging.DEBUG)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

        _safe_symlink("main.txt", boss_dir / boss_full)

        _registry[logger_key] = logger
        return logger


def shutdown_logger() -> None:
    with _lock:
        for logger in _registry.values():
            for handler in logger.handlers[:]:
                handler.flush()
                logger.removeHandler(handler)
        for handler in _file_handlers.values():
            handler.flush()
            handler.close()
        _registry.clear()
        _file_handlers.clear()
    logging.shutdown()