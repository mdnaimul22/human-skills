from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from src.helpers import ValidationError
from src.apps.certbot.helpers.issuer import Issuer
from src.apps.certbot.helpers.schema import CertificateBundle


def test_issue_empty_domain() -> None:
    with pytest.raises(ValidationError):
        Issuer.issue("   ")


def test_issue_invalid_domain_format() -> None:
    with pytest.raises(ValidationError):
        Issuer.issue("--inject-param")
    with pytest.raises(ValidationError):
        Issuer.issue("example.com", extra_domains=["--bad-param"])


def test_issue_dry_run_success() -> None:
    mock_res = MagicMock(returncode=0, stdout="Dry run succeeded", stderr="")
    with patch("subprocess.run", return_value=mock_res) as mock_run, \
         patch("src.apps.certbot.helpers.issuer.ensure_dir"):
        bundle = Issuer.issue("example.com", dry_run=True)
        assert bundle.domain == "example.com"
        assert bundle.status == "DRY_RUN_SUCCESS"
        assert bundle.is_valid is True
        assert bundle.needs_renewal is False

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "--dry-run" in cmd
        assert "--webroot" in cmd
        assert "-w" in cmd
        assert "/var/www/html" in cmd
        assert "-d" in cmd
        assert "example.com" in cmd


def test_issue_failure_returncode() -> None:
    mock_res = MagicMock(returncode=1, stdout="", stderr="HTTP challenge timeout error")
    with patch("subprocess.run", return_value=mock_res), \
         patch("src.apps.certbot.helpers.issuer.ensure_dir"):
        bundle = Issuer.issue("example.com", dry_run=False)
        assert bundle.domain == "example.com"
        assert bundle.status == "FAILED"
        assert bundle.is_valid is False
        assert bundle.needs_renewal is True


def test_issue_success_calls_auditor() -> None:
    mock_res = MagicMock(returncode=0, stdout="Success", stderr="")
    mock_bundle = CertificateBundle(
        domain="example.com",
        fullchain_path="/etc/letsencrypt/live/example.com/fullchain.pem",
        privkey_path="/etc/letsencrypt/live/example.com/privkey.pem",
        status="VALID",
        is_valid=True,
        needs_renewal=False,
    )

    with patch("subprocess.run", return_value=mock_res), \
         patch("src.apps.certbot.helpers.issuer.ensure_dir"), \
         patch("src.apps.certbot.helpers.issuer.Auditor.audit", return_value=mock_bundle) as mock_audit:
        bundle = Issuer.issue("example.com", extra_domains=["www.example.com"], dry_run=False)
        assert bundle.status == "VALID"
        assert bundle.is_valid is True
        mock_audit.assert_called_once_with("example.com", certs_dir=Issuer.DEFAULT_CERTS_DIR)


def test_issue_subprocess_exception() -> None:
    with patch("subprocess.run", side_effect=RuntimeError("Subprocess execution error")), \
         patch("src.apps.certbot.helpers.issuer.ensure_dir"):
        bundle = Issuer.issue("example.com")
        assert bundle.status == "FAILED"
        assert bundle.is_valid is False
        assert bundle.needs_renewal is True


def test_issue_command_args_construction() -> None:
    mock_res = MagicMock(returncode=0, stdout="Dry run succeeded", stderr="")
    with patch("subprocess.run", return_value=mock_res) as mock_run, \
         patch("src.apps.certbot.helpers.issuer.ensure_dir"):
        Issuer.issue(
            domain="example.com",
            extra_domains=["www.example.com", "api.example.com"],
            email="custom@example.com",
            webroot_path="/custom/webroot",
            dry_run=True,
        )

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        cmd_str = " ".join(cmd)
        assert "--webroot" in cmd_str
        assert "-w /custom/webroot" in cmd_str
        assert "-m custom@example.com" in cmd_str
        assert "-d example.com" in cmd_str
        assert "-d www.example.com" in cmd_str
        assert "-d api.example.com" in cmd_str
        assert "--dry-run" in cmd_str
