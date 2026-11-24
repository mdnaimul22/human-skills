from __future__ import annotations

from unittest.mock import MagicMock, patch
from src.apps.certbot.manager import CertbotManager, get_certbot_manager
from src.apps.certbot.helpers.schema import CertificateBundle, SslAuditReport


def test_manager_singleton() -> None:
    CertbotManager.reset_instance()
    m1 = CertbotManager()
    m2 = CertbotManager()
    assert m1 is m2
    assert get_certbot_manager() is m1


def test_get_certificate_delegation() -> None:
    CertbotManager.reset_instance()
    mgr = CertbotManager()

    mock_bundle = CertificateBundle(
        domain="example.com",
        status="VALID",
        is_valid=True,
        needs_renewal=False,
    )
    with patch("src.apps.certbot.manager.Auditor.audit", return_value=mock_bundle) as mock_audit:
        res = mgr.get_certificate("example.com")
        assert res.domain == "example.com"
        assert res.is_valid is True
        mock_audit.assert_called_once_with("example.com")


def test_ensure_certificate_skips_when_valid() -> None:
    CertbotManager.reset_instance()
    mgr = CertbotManager()

    valid_bundle = CertificateBundle(
        domain="example.com",
        status="VALID",
        days_remaining=80,
        is_valid=True,
        needs_renewal=False,
    )

    with patch("src.apps.certbot.manager.Auditor.audit", return_value=valid_bundle), \
         patch("src.apps.certbot.manager.Issuer.issue") as mock_issue:
        res = mgr.ensure_certificate("example.com")
        assert res.status == "VALID"
        assert res.is_valid is True
        mock_issue.assert_not_called()


def test_ensure_certificate_executes_when_needed() -> None:
    CertbotManager.reset_instance()
    mgr = CertbotManager()

    missing_bundle = CertificateBundle(
        domain="example.com",
        status="NOT_FOUND",
        is_valid=False,
        needs_renewal=True,
    )
    newly_issued = CertificateBundle(
        domain="example.com",
        status="VALID",
        days_remaining=90,
        is_valid=True,
        needs_renewal=False,
    )

    with patch("src.apps.certbot.manager.Auditor.audit", return_value=missing_bundle), \
         patch("src.apps.certbot.manager.Issuer.issue", return_value=newly_issued) as mock_issue:
        res = mgr.ensure_certificate("example.com", extra_domains=["www.example.com"], dry_run=True)
        assert res.status == "VALID"
        assert res.is_valid is True
        mock_issue.assert_called_once_with(
            domain="example.com",
            extra_domains=["www.example.com"],
            dry_run=True,
        )


def test_ensure_certificate_executes_when_force_flag_set() -> None:
    CertbotManager.reset_instance()
    mgr = CertbotManager()

    valid_bundle = CertificateBundle(
        domain="example.com",
        status="VALID",
        days_remaining=85,
        is_valid=True,
        needs_renewal=False,
    )
    forced_bundle = CertificateBundle(
        domain="example.com",
        status="VALID",
        days_remaining=90,
        is_valid=True,
        needs_renewal=False,
    )

    with patch("src.apps.certbot.manager.Auditor.audit", return_value=valid_bundle), \
         patch("src.apps.certbot.manager.Issuer.issue", return_value=forced_bundle) as mock_issue:
        res = mgr.ensure_certificate("example.com", force=True)
        assert res.status == "VALID"
        mock_issue.assert_called_once()


def test_audit_all_delegation() -> None:
    CertbotManager.reset_instance()
    mgr = CertbotManager()

    mock_report = SslAuditReport(
        all_valid=True,
        requires_action=False,
        audited_at="2026-11-17T02:00:00Z",
    )
    with patch("src.apps.certbot.manager.Auditor.audit_all", return_value=mock_report) as mock_audit:
        res = mgr.audit_all(["example.com", "api.example.com"])
        assert res.all_valid is True
        mock_audit.assert_called_once_with(["example.com", "api.example.com"])


def test_is_ssl_active() -> None:
    CertbotManager.reset_instance()
    mgr = CertbotManager()

    active_bundle = CertificateBundle(domain="example.com", is_valid=True)
    inactive_bundle = CertificateBundle(domain="example.com", is_valid=False)

    with patch.object(mgr, "get_certificate", return_value=active_bundle):
        assert mgr.is_ssl_active("example.com") is True

    with patch.object(mgr, "get_certificate", return_value=inactive_bundle):
        assert mgr.is_ssl_active("example.com") is False
