import json
import logging
import os
import sys
import uuid
import src.config.logger as cfg_logger
from src.config import (
    JsonLinesFormatter,
    PROJECT_ROOT,
    SanitizingFormatter,
    delete,
    get_abs_path,
    read_text,
    sanitize_log_text,
    setup_logger,
)
from src.config.logger import ColorFormatter


def _make_record(msg: str, exc_info: object = None, extra: dict[str, object] | None = None) -> logging.LogRecord:
    record = logging.LogRecord(
        name="tests.logger_sanitization",
        level=logging.ERROR,
        pathname=get_abs_path("src/sample.py"),
        lineno=42,
        msg=msg,
        args=(),
        exc_info=exc_info,  # type: ignore[arg-type]
    )
    if extra:
        for k, v in extra.items():
            setattr(record, k, v)
    return record


def test_sanitize_log_text_project_root_and_home() -> None:
    root_str = str(PROJECT_ROOT)
    home_str = os.path.expanduser("~")

    assert sanitize_log_text(f"Loaded {root_str}/data/ffmpeg/bin/ffmpeg") == "Loaded <PROJECT_ROOT>/data/ffmpeg/bin/ffmpeg"
    assert sanitize_log_text(f"bin={root_str}") == "bin=<PROJECT_ROOT>"

    sibling = f"{root_str}_other/a"
    assert sanitize_log_text(sibling) == f"<HOME>/{os.path.basename(root_str)}_other/a"
    assert "<PROJECT_ROOT>_other" not in sanitize_log_text(sibling)

    assert sanitize_log_text(f"{home_str}/miniconda3/bin/yt-dlp") == "<HOME>/miniconda3/bin/yt-dlp"
    assert sanitize_log_text("/home/otheruser/x") == "<HOME>/x"
    assert sanitize_log_text("/Users/dev/x") == "<HOME>/x"

    url1 = "https://example.com/home/naimul/profile"
    url2 = "http://localhost:8000/home/test"
    assert sanitize_log_text(url1) == url1
    assert sanitize_log_text(url2) == url2


def test_plain_and_color_formatters_sanitize_message_and_traceback() -> None:
    root_str = str(PROJECT_ROOT)
    home_str = os.path.expanduser("~")

    plain = SanitizingFormatter(fmt="%(levelname)s %(message)s")
    color = ColorFormatter(fmt="%(levelname)s %(message)s")

    try:
        raise RuntimeError(f"boom at {root_str}/tmp/file.mp4 and {home_str}/miniconda3/bin/yt-dlp")
    except RuntimeError:
        exc_info = sys.exc_info()

    rec = _make_record(f"failed reading {root_str}/data/x and {home_str}/bin/y", exc_info=exc_info)
    for fmt in (plain, color):
        formatted = fmt.format(rec)
        assert root_str not in formatted
        assert home_str not in formatted
        assert "<PROJECT_ROOT>/data/x" in formatted
        assert "<PROJECT_ROOT>/tmp/file.mp4" in formatted
        assert "<HOME>/bin/y" in formatted
        assert "<HOME>/miniconda3/bin/yt-dlp" in formatted


def test_json_lines_formatter_sanitizes_message_error_and_metadata() -> None:
    root_str = str(PROJECT_ROOT)
    home_str = os.path.expanduser("~")
    formatter = JsonLinesFormatter()

    try:
        raise ValueError(f"bad path {root_str}/tmp/in.mp4")
    except ValueError:
        exc_info = sys.exc_info()

    rec = _make_record(
        f"exec {home_str}/miniconda3/bin/yt-dlp {root_str}/src/plugins",
        exc_info=exc_info,
        extra={
            "metadata": {
                "nested": {"bin": f"{home_str}/miniconda3/bin/python", "items": [f"{root_str}/data/a", 123]},
                "root_obj": PROJECT_ROOT,
                f"{root_str}/key": f"{root_str}/val",
            },
            "custom_path": f"{root_str}/tmp/out.mp4",
        },
    )
    raw_line = formatter.format(rec)
    assert root_str not in raw_line
    assert home_str not in raw_line

    payload = json.loads(raw_line)
    assert payload["message"] == "exec <HOME>/miniconda3/bin/yt-dlp <PROJECT_ROOT>/src/plugins"
    assert "<PROJECT_ROOT>/tmp/in.mp4" in payload["error"]["message"]
    assert "<PROJECT_ROOT>" in payload["error"]["stack"]
    assert payload["metadata"]["nested"]["bin"] == "<HOME>/miniconda3/bin/python"
    assert payload["metadata"]["nested"]["items"] == ["<PROJECT_ROOT>/data/a", 123]
    assert payload["metadata"]["root_obj"] == "<PROJECT_ROOT>"
    assert payload["metadata"]["<PROJECT_ROOT>/key"] == "<PROJECT_ROOT>/val"
    assert payload["metadata"]["custom_path"] == "<PROJECT_ROOT>/tmp/out.mp4"


def test_setup_logger_end_to_end_files_contain_no_host_paths() -> None:
    root_str = str(PROJECT_ROOT)
    home_str = os.path.expanduser("~")
    rel_dir = f"tmp/test_tmp/logger_san_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    rel_log = f"{rel_dir}/test.log"
    rel_tel = f"{rel_dir}/telemetry.jsonl"
    abs_log = get_abs_path(rel_log)
    abs_tel = get_abs_path(rel_tel)
    logger_name = f"tests.e2e_san_{os.getpid()}_{uuid.uuid4().hex[:6]}"

    test_logger = setup_logger(abs_log, name=logger_name)
    try:
        test_logger.info(
            f"path={root_str}/data/cookies.txt home={home_str}/miniconda3/bin/yt-dlp",
            extra={"metadata": {"target": f"{root_str}/tmp/video.mp4"}},
        )
        try:
            raise OSError(f"cannot read {root_str}/data/missing")
        except OSError:
            test_logger.error(f"exception for {home_str}/file", exc_info=True)

        for handler in test_logger.handlers:
            handler.flush()

        plain_text = read_text(rel_log)
        tel_text = read_text(rel_tel)

        assert plain_text.strip()
        assert tel_text.strip()
        assert root_str not in plain_text
        assert home_str not in plain_text
        assert root_str not in tel_text
        assert home_str not in tel_text
        assert "<PROJECT_ROOT>/data/cookies.txt" in plain_text
        assert "<HOME>/miniconda3/bin/yt-dlp" in plain_text
    finally:
        with cfg_logger._lock:
            cfg_logger._registry.pop(logger_name, None)
            for handler in test_logger.handlers[:]:
                handler.flush()
                test_logger.removeHandler(handler)
            for key in list(cfg_logger._file_handlers.keys()):
                if key in {abs_log, abs_tel}:
                    h = cfg_logger._file_handlers.pop(key)
                    h.flush()
                    h.close()
        delete(rel_dir)
