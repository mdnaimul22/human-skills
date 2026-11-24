from __future__ import annotations

from unittest.mock import MagicMock, patch
from src.apps.nginx.helpers.service import Service


def test_test_syntax_success() -> None:
    mock_run = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_run):
        assert Service.test_syntax() is True


def test_test_syntax_failure() -> None:
    mock_run = MagicMock(returncode=1, stderr="syntax error")
    with patch("subprocess.run", return_value=mock_run):
        assert Service.test_syntax() is False


def test_test_syntax_exception() -> None:
    with patch("subprocess.run", side_effect=RuntimeError("exec error")):
        assert Service.test_syntax() is False


def test_reload_success_first_attempt() -> None:
    mock_run = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_run):
        assert Service.reload() is True


def test_reload_fallback_to_restart_success() -> None:
    mock_fail = MagicMock(returncode=1)
    mock_succ = MagicMock(returncode=0)
    with patch("subprocess.run", side_effect=[mock_fail, mock_succ]):
        assert Service.reload() is True


def test_reload_both_fail() -> None:
    mock_fail = MagicMock(returncode=1, stderr="service not found")
    with patch("subprocess.run", side_effect=[mock_fail, mock_fail]):
        assert Service.reload() is False


def test_reload_exception() -> None:
    with patch("subprocess.run", side_effect=RuntimeError("systemctl dead")):
        assert Service.reload() is False


def test_is_running() -> None:
    with patch("subprocess.run", return_value=MagicMock(returncode=0)):
        assert Service.is_running() is True
    with patch("subprocess.run", return_value=MagicMock(returncode=1)):
        assert Service.is_running() is False
    with patch("subprocess.run", side_effect=RuntimeError("err")):
        assert Service.is_running() is False


def test_test_and_reload_passes() -> None:
    with patch.object(Service, "test_syntax", return_value=True), patch.object(
        Service, "reload", return_value=True
    ):
        assert Service.test_and_reload() is True


def test_test_and_reload_fails_syntax() -> None:
    with patch.object(Service, "test_syntax", return_value=False):
        assert Service.test_and_reload() is False


def test_probe_health_success() -> None:
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert Service.probe_health(timeout=1.0) is True


def test_probe_health_timeout() -> None:
    with patch("urllib.request.urlopen", side_effect=Exception("connection refused")), patch("time.sleep"):
        assert Service.probe_health(timeout=0.1) is False


def test_start_health_probe_starts_thread() -> None:
    with patch("threading.Thread") as mock_thread:
        Service.start_health_probe(timeout=5.0)
        assert mock_thread.call_count == 1
