from __future__ import annotations

import json
import logging
import math
import re
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Iterator

from .files import ensure_dir
from .paths import PROJECT_ROOT

_NOISY_LOGGERS: tuple[str, ...] = (
    "httpx", "openai", "anthropic", "httpcore",
    "urllib3", "asyncio", "multipart",
)

_lock = threading.Lock()
_registry: dict[str, logging.Logger] = {}
_file_handlers: dict[str, RotatingFileHandler] = {}
_configured_dirs: set[Path] = set()

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
telemetry_ctx: ContextVar[dict[str, Any]] = ContextVar("telemetry_ctx", default={})


def _build_path_rules() -> tuple[tuple[re.Pattern[str], str], ...]:
    prefix_guard = r"(?<![A-Za-z0-9_.\-])"
    boundary = r"(?=$|[/\\\s\"',;:)\]}])"
    raw_entries: list[tuple[str, str]] = []
    seen: set[str] = set()

    for candidate in (PROJECT_ROOT, PROJECT_ROOT.resolve()):
        text = str(candidate).rstrip("/\\")
        if text and text != "/" and text not in seen:
            seen.add(text)
            raw_entries.append((text, "<PROJECT_ROOT>"))

    try:
        home_path = Path.home()
        home_candidates = [home_path, home_path.resolve()]
    except RuntimeError:
        home_candidates = []

    for candidate in home_candidates:
        text = str(candidate).rstrip("/\\")
        if text and text != "/" and text not in seen:
            seen.add(text)
            raw_entries.append((text, "<HOME>"))

    raw_entries.sort(key=lambda item: len(item[0]), reverse=True)
    rules: list[tuple[re.Pattern[str], str]] = [
        (re.compile(rf"{prefix_guard}{re.escape(path_str)}{boundary}"), token)
        for path_str, token in raw_entries
    ]
    user_segment = r"[^/\s\"'\\,:;)\]}]+"
    rules.append((re.compile(rf"{prefix_guard}/(?:home|Users)/{user_segment}{boundary}"), "<HOME>"))
    return tuple(rules)


_PATH_RULES: tuple[tuple[re.Pattern[str], str], ...] = _build_path_rules()


def sanitize_log_text(text: str) -> str:
    if "/" not in text and "\\" not in text:
        return text
    result = text
    for pattern, replacement in _PATH_RULES:
        result = pattern.sub(replacement, result)
    return result


def _safe_str(val: Any) -> str:
    try:
        return str(val)
    except Exception:
        try:
            return repr(val)
        except Exception:
            return f"<{type(val).__name__} at {hex(id(val))}>"


def _sanitize_key(key: Any) -> str:
    match key:
        case str():
            return sanitize_log_text(key)
        case _:
            return sanitize_log_text(_safe_str(key))


def _sanitize_value(val: Any) -> Any:
    match val:
        case str():
            return sanitize_log_text(val)
        case Path():
            return sanitize_log_text(str(val))
        case dict():
            return {_sanitize_key(k): _sanitize_value(v) for k, v in val.items()}
        case list() | tuple() | set() | frozenset():
            return [_sanitize_value(item) for item in val]
        case _:
            return val


def _safe_default(val: Any) -> Any:
    if isinstance(val, Path):
        return sanitize_log_text(str(val))
    if hasattr(val, "isoformat"):
        try:
            return val.isoformat()
        except Exception:
            return sanitize_log_text(_safe_str(val))
    if hasattr(val, "value"):
        raw_val = val.value
        return sanitize_log_text(raw_val) if isinstance(raw_val, str) else raw_val
    if isinstance(val, (set, frozenset)):
        return [_sanitize_value(item) for item in val]
    return sanitize_log_text(_safe_str(val))


@contextmanager
def job_context(job_id: str) -> Iterator[str]:
    token = request_id_ctx.set(job_id)
    token_tel = set_telemetry(job_id=job_id, request_id=job_id)
    try:
        yield job_id
    finally:
        request_id_ctx.reset(token)
        reset_telemetry(token_tel)


def get_telemetry() -> dict[str, Any]:
    return dict(telemetry_ctx.get())


def set_telemetry(**kwargs: Any) -> Any:
    if "request_id" in kwargs:
        request_id_ctx.set(kwargs["request_id"])
    current = dict(telemetry_ctx.get())
    for k, v in kwargs.items():
        if v is None:
            current.pop(k, None)
        else:
            current[k] = v
    return telemetry_ctx.set(current)


def reset_telemetry(token: Any) -> None:
    if token is not None:
        try:
            telemetry_ctx.reset(token)
        except (ValueError, RuntimeError):
            pass


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_ctx.get()
        return True


class SanitizingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return sanitize_log_text(super().format(record))


class ColorFormatter(SanitizingFormatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        orig = record.levelname
        padded = f"{orig:<5}"
        color = self.COLORS.get(orig)
        record.levelname = f"{color}{padded}{self.RESET}" if color else padded
        try:
            return super().format(record)
        finally:
            record.levelname = orig


class JsonLinesFormatter(logging.Formatter):
    def _store_sanitized(self, target: dict[str, Any], key: Any, val: Any) -> None:
        safe_k = _sanitize_key(key)
        try:
            json.dumps(val, default=_safe_default)
            target[safe_k] = _sanitize_value(val)
        except (TypeError, OverflowError, ValueError):
            target[safe_k] = sanitize_log_text(_safe_str(val))

    def _extract_metadata(self, record: logging.LogRecord) -> dict[str, Any]:
        STANDARD_RECORD_ATTRS: set[str] = {
            "name", "msg", "args", "levelname", "levelno",
            "pathname", "filename", "module", "exc_info",
            "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread",
            "threadName", "processName", "process", "message",
            "request_id", "job_id", "user_id", "client_ip",
            "service", "endpoint", "duration_ms",
        }
        metadata: dict[str, Any] = {}
        if hasattr(record, "metadata") and isinstance(record.metadata, dict):
            for k, v in record.metadata.items():
                self._store_sanitized(metadata, k, v)

        for key, val in record.__dict__.items():
            if key not in STANDARD_RECORD_ATTRS and not key.startswith("_"):
                self._store_sanitized(metadata, key, val)
        return metadata

    def format(self, record: logging.LogRecord) -> str:
        try:
            msg = record.getMessage()
        except Exception:
            msg = str(record.msg)
        safe_msg = sanitize_log_text(msg)

        req_id = getattr(record, "request_id", None)
        if req_id == "-":
            req_id = None
        job_id = getattr(record, "job_id", None)
        if not job_id and req_id:
            job_id = req_id

        duration_ms = getattr(record, "duration_ms", None)
        if isinstance(duration_ms, (int, float)):
            if math.isnan(duration_ms) or math.isinf(duration_ms):
                duration_ms = None
            else:
                duration_ms = round(float(duration_ms), 3)
        else:
            duration_ms = None

        meta = self._extract_metadata(record)

        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "epoch": record.created,
            "level": record.levelname,
            "logger": record.name,
            "message": safe_msg,
            "request_id": req_id,
            "job_id": job_id,
            "user_id": getattr(record, "user_id", None),
            "client_ip": getattr(record, "client_ip", None),
            "service": getattr(record, "service", None),
            "endpoint": getattr(record, "endpoint", None),
            "duration_ms": duration_ms,
            "error": self._extract_error(record),
            "metadata": meta,
        }

        try:
            return json.dumps(payload, ensure_ascii=False, default=_safe_default)
        except (TypeError, OverflowError, ValueError) as dump_err:
            fallback_payload = {
                "timestamp": payload["timestamp"],
                "epoch": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": sanitize_log_text(_safe_str(safe_msg)),
                "request_id": _safe_str(req_id) if req_id else None,
                "job_id": _safe_str(job_id) if job_id else None,
                "user_id": _safe_str(getattr(record, "user_id", None)) if getattr(record, "user_id", None) else None,
                "client_ip": _safe_str(getattr(record, "client_ip", None)) if getattr(record, "client_ip", None) else None,
                "service": _safe_str(getattr(record, "service", None)) if getattr(record, "service", None) else None,
                "endpoint": _safe_str(getattr(record, "endpoint", None)) if getattr(record, "endpoint", None) else None,
                "duration_ms": duration_ms,
                "error": {"type": "SerializationError", "message": sanitize_log_text(_safe_str(dump_err))},
                "metadata": {"raw_metadata": sanitize_log_text(_safe_str(record.__dict__.get("metadata")))},
            }
            return json.dumps(fallback_payload, ensure_ascii=False, default=_safe_str)

    def _extract_error(self, record: logging.LogRecord) -> dict[str, Any] | None:
        if record.exc_info:
            exc_type, exc_val, exc_tb = record.exc_info
            return {
                "type": getattr(exc_type, "__name__", "Exception") if exc_type else "Exception",
                "message": sanitize_log_text(_safe_str(exc_val)),
                "stack": sanitize_log_text(traceback.format_exc()) if exc_tb else None,
            }
        if record.levelno >= logging.ERROR:
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(record.msg)
            return {
                "type": record.levelname,
                "message": sanitize_log_text(msg),
                "stack": None,
            }
        return None


def _build_formatter() -> logging.Formatter:
    return ColorFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
    )


def _build_plain_formatter() -> logging.Formatter:
    return SanitizingFormatter(
        fmt="%(asctime)s %(levelname)-5s %(name)s %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
    )


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
    for prefix in ("app.", "src.", "myproject.", "chaincv.", "vidula."):
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


def uvicorn_logging() -> None:
    try:
        import uvicorn.config

        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
        datefmt = "%d-%m-%y %H:%M:%S"

        uv_cfg = uvicorn.config.LOGGING_CONFIG
        if "formatters" in uv_cfg:
            formatter_dict = {
                "()": "src.config.logger.ColorFormatter",
                "fmt": fmt,
                "datefmt": datefmt,
            }
            if "default" in uv_cfg["formatters"]:
                uv_cfg["formatters"]["default"] = dict(formatter_dict)
            if "access" in uv_cfg["formatters"]:
                uv_cfg["formatters"]["access"] = dict(formatter_dict)

        color_formatter = ColorFormatter(fmt=fmt, datefmt=datefmt)
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            uv_logger = logging.getLogger(name)
            for handler in uv_logger.handlers:
                handler.setFormatter(color_formatter)
    except Exception as err:
        _ = str(err)


def _configure_system(log_dir: Path, is_production: bool) -> None:
    if log_dir in _configured_dirs:
        return

    root = logging.getLogger()
    root.setLevel(logging.INFO if is_production else logging.DEBUG)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    uvicorn_logging()
    ensure_dir(str(log_dir))
    _configured_dirs.add(log_dir)


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

    ensure_dir(str(file_path.parent))
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
    boss_name: Path | str | None = None,
    his_name: str | None = None,
    *,
    log_path: Path | str | None = None,
    name: str | None = None,
    enable_telemetry: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    **kwargs: Any,
) -> logging.Logger:
    explicit_name = name or kwargs.get("name")

    if boss_name is None:
        if log_path is not None:
            boss_name = log_path
        elif explicit_name:
            boss_name = f"{explicit_name}.log"
        else:
            boss_name = "main.txt"

    if explicit_name:
        logger_key = str(explicit_name)
    elif his_name is not None:
        logger_key = _resolve_target(str(his_name), Path("logs"))[3]
    elif isinstance(boss_name, str) and not ("/" in boss_name or "\\" in boss_name):
        logger_key = _resolve_target(boss_name, Path("logs"))[3]
    else:
        logger_key = Path(str(boss_name)).stem

    if logger_key in _registry:
        return _registry[logger_key]

    with _lock:
        if logger_key in _registry:
            return _registry[logger_key]

        from .settings import Settings

        is_prod: bool = Settings.is_production
        log_dir: Path = Settings.LOG_DIR

        _configure_system(log_dir, is_prod)

        logger = logging.getLogger(logger_key)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        if not any(isinstance(f, CorrelationIdFilter) for f in logger.filters):
            logger.addFilter(CorrelationIdFilter())

        if logger.handlers:
            _registry[logger_key] = logger
            return logger

        plain_fmt = _build_plain_formatter()

        is_named_spec = his_name is not None or (
            isinstance(boss_name, str)
            and ("main.txt" in boss_name or ("." in boss_name and "/" not in boss_name and "\\" not in boss_name))
        )

        if is_named_spec:
            boss_dir, boss_full, boss_alias, _ = _resolve_target(str(boss_name), log_dir, default_base="main.txt")
            boss_path = boss_dir / "main.txt"
            boss_handler = _get_or_create_handler(
                boss_path, is_prod, plain_fmt, max_bytes=max_bytes, backup_count=backup_count
            )
            if boss_handler not in logger.handlers:
                logger.addHandler(boss_handler)

            if his_name is not None:
                his_dir, his_full, his_alias, _ = _resolve_target(str(his_name), log_dir, default_base="main.txt")
                his_path = his_dir / his_full
                if his_path.resolve() != boss_path.resolve():
                    his_handler = _get_or_create_handler(
                        his_path, is_prod, plain_fmt, max_bytes=max_bytes, backup_count=backup_count
                    )
                    if his_handler not in logger.handlers:
                        logger.addHandler(his_handler)
                if his_full != his_alias:
                    _safe_symlink(his_full, his_dir / his_alias)

            _safe_symlink("main.txt", boss_dir / boss_full)
            target_path = boss_path
        else:
            target_path = Path(boss_name) if isinstance(boss_name, (str, Path)) else log_dir / "app.log"
            if not target_path.is_absolute():
                target_path = log_dir / target_path
            target_handler = _get_or_create_handler(
                target_path, is_prod, plain_fmt, max_bytes=max_bytes, backup_count=backup_count
            )
            if target_handler not in logger.handlers:
                logger.addHandler(target_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING if is_prod else logging.DEBUG)
        console_handler.setFormatter(_build_formatter())
        logger.addHandler(console_handler)

        if enable_telemetry:
            telemetry_dir = target_path.parent if target_path.is_absolute() else log_dir
            telemetry_path = telemetry_dir / "telemetry.jsonl"
            if target_path.resolve() != telemetry_path.resolve():
                telemetry_handler = _get_or_create_handler(
                    telemetry_path, is_prod, JsonLinesFormatter(),
                    max_bytes=max_bytes, backup_count=backup_count,
                )
                if telemetry_handler not in logger.handlers:
                    logger.addHandler(telemetry_handler)

        _registry[logger_key] = logger
        return logger


@contextmanager
def measure_latency(
    operation: str,
    *,
    logger: logging.Logger | None = None,
    extra: dict[str, Any] | None = None,
    level: int = logging.INFO,
) -> Iterator[dict[str, Any]]:
    start = time.perf_counter()
    metrics: dict[str, Any] = {"operation": operation}
    if extra:
        metrics.update(extra)
    try:
        yield metrics
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        metrics["duration_ms"] = round(elapsed_ms, 3)
        if logger is not None:
            log_extra = dict(metrics)
            logger.log(
                level,
                f"Completed {operation} in {elapsed_ms:.2f}ms",
                extra=log_extra,
            )


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
        _configured_dirs.clear()
    logging.shutdown()
