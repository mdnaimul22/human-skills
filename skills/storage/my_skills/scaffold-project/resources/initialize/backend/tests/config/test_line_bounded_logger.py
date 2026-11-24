from __future__ import annotations
import os
import uuid
import pytest
from src.config import PROJECT_ROOT, delete, ensure_dir, get_abs_path, read_text, setup_logger, shutdown_logger
from src.config.logger import LineBoundedRotatingHandler


def test_line_bounded_handler_prunes_only_on_threshold(tmp_path) -> None:
    shutdown_logger()
    log_file = tmp_path / "bounded.log"
    logger_name = f"tests.bounded_{uuid.uuid4().hex[:8]}"

    test_logger = setup_logger(str(log_file), name=logger_name, limit=10, threshold=15)
    handler = [h for h in test_logger.handlers if isinstance(h, LineBoundedRotatingHandler)][0]
    handler.check_interval = 2

    for i in range(14):
        test_logger.info(f"msg_{i}")
    for h in test_logger.handlers:
        h.flush()

    with open(str(log_file)) as f:
        lines = f.readlines()
    assert len(lines) == 14

    test_logger.info("msg_14")
    test_logger.info("msg_15")
    for h in test_logger.handlers:
        h.flush()

    with open(str(log_file)) as f:
        lines = [line.strip() for line in f.readlines()]
    assert len(lines) == 10
    assert lines[0].endswith("msg_6")
    assert lines[-1].endswith("msg_15")
    shutdown_logger()


def test_line_bounded_handler_prunes_preexisting_file(tmp_path) -> None:
    shutdown_logger()
    log_file = tmp_path / "preexisting.log"
    with open(str(log_file), "w") as f:
        for i in range(50):
            f.write(f"old_line_{i}\n")

    logger_name = f"tests.pre_{uuid.uuid4().hex[:8]}"
    test_logger = setup_logger(str(log_file), name=logger_name, limit=10, threshold=15)
    for h in test_logger.handlers:
        h.flush()

    with open(str(log_file)) as f:
        lines = [line.strip() for line in f.readlines()]
    assert len(lines) == 10
    assert lines[0] == "old_line_40"
    assert lines[-1] == "old_line_49"
    shutdown_logger()


def test_setup_logger_without_limit_uses_standard_handler(tmp_path) -> None:
    shutdown_logger()
    log_file = tmp_path / "standard.log"
    logger_name = f"tests.std_{uuid.uuid4().hex[:8]}"

    test_logger = setup_logger(str(log_file), name=logger_name)
    bounded_handlers = [h for h in test_logger.handlers if isinstance(h, LineBoundedRotatingHandler)]
    assert len(bounded_handlers) == 0
    shutdown_logger()
