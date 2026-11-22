import json
import logging
import os
import sys
import uuid
from src.config.paths import PROJECT_ROOT
from src.config.files import read_text, exists, delete, get_abs_path
from src.config.logger import (
    sanitize_log_text,
    setup_logger,
    shutdown_logger,
    job_context,
    get_telemetry,
    set_telemetry,
    reset_telemetry,
    measure_latency,
    SanitizingFormatter,
    ColorFormatter,
    JsonLinesFormatter,
)


def _make_record(msg: str, exc_info: object = None, extra: dict[str, object] | None = None) -> logging.LogRecord:
    record = logging.LogRecord(
        name="tests.logger",
        level=logging.ERROR,
        pathname=get_abs_path("src/config/logger.py"),
        lineno=42,
        msg=msg,
        args=(),
        exc_info=exc_info,  # type: ignore[arg-type]
    )
    if extra:
        for k, v in extra.items():
            setattr(record, k, v)
    return record


def test_sanitize_log_text_masks_root_and_home() -> None:
    root_str = str(PROJECT_ROOT)
    home_str = os.path.expanduser("~")

    raw = f"Loaded {root_str}/src/config/logger.py from {home_str}/user_data"
    sanitized = sanitize_log_text(raw)
    assert "<PROJECT_ROOT>/src/config/logger.py" in sanitized
    assert "<HOME>/user_data" in sanitized
    assert root_str not in sanitized
    assert home_str not in sanitized


def test_sanitizing_and_color_formatters() -> None:
    root_str = str(PROJECT_ROOT)
    home_str = os.path.expanduser("~")

    plain = SanitizingFormatter(fmt="%(levelname)s %(message)s")
    color = ColorFormatter(fmt="%(levelname)s %(message)s")

    try:
        raise RuntimeError(f"crash at {root_str}/src/fail.py and {home_str}/tool")
    except RuntimeError:
        exc_info = sys.exc_info()

    rec = _make_record(f"error in {root_str}/core and {home_str}/bin", exc_info=exc_info)
    for fmt in (plain, color):
        formatted = fmt.format(rec)
        assert root_str not in formatted
        assert home_str not in formatted
        assert "<PROJECT_ROOT>" in formatted
        assert "<HOME>" in formatted


def test_json_lines_formatter_sanitization() -> None:
    root_str = str(PROJECT_ROOT)
    home_str = os.path.expanduser("~")
    formatter = JsonLinesFormatter()

    rec = _make_record(
        f"job failed at {root_str}/data",
        extra={
            "metadata": {
                "bin": f"{home_str}/bin/python",
                "nested": [f"{root_str}/output.json", 100],
            }
        },
    )
    raw_line = formatter.format(rec)
    assert root_str not in raw_line
    assert home_str not in raw_line

    payload = json.loads(raw_line)
    assert "<PROJECT_ROOT>/data" in payload["message"]
    assert payload["metadata"]["bin"] == "<HOME>/bin/python"
    assert payload["metadata"]["nested"][0] == "<PROJECT_ROOT>/output.json"


def test_setup_logger_with_boss_and_his_name() -> None:
    test_id = uuid.uuid4().hex[:6]
    boss = f"routers.main_{test_id}.txt"
    his = f"routers.agent_{test_id}.txt"

    test_logger = setup_logger(boss_name=boss, his_name=his)
    test_logger.info("Message through boss-his logger")

    for h in test_logger.handlers:
        h.flush()

    boss_path = f"logs/routers/main.txt"
    assert exists(boss_path)


def test_telemetry_lifecycle() -> None:
    assert get_telemetry() == {}
    token = set_telemetry(tenant_id="tenant_1", request_id="req_999")
    current = get_telemetry()
    assert current["tenant_id"] == "tenant_1"
    assert current["request_id"] == "req_999"

    reset_telemetry(token)
    assert get_telemetry() == {}


def test_job_context() -> None:
    with job_context("job_abc_123") as j_id:
        assert j_id == "job_abc_123"
        tel = get_telemetry()
        assert tel["job_id"] == "job_abc_123"

    assert get_telemetry() == {}


def test_measure_latency() -> None:
    logger = logging.getLogger("tests.latency")
    with measure_latency("benchmark_task", logger=logger) as metrics:
        total = sum(i for i in range(1000))
        assert total > 0

    assert "duration_ms" in metrics
    assert metrics["duration_ms"] >= 0.0
