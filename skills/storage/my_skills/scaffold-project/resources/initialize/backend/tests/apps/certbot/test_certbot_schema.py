from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.apps.certbot.helpers.schema import (
    CERTIFICATE_BUNDLE_ADAPTER,
    SSL_AUDIT_REPORT_ADAPTER,
    CertificateBundle,
    SslAuditReport,
)


def test_certificate_bundle_defaults() -> None:
    bundle = CERTIFICATE_BUNDLE_ADAPTER.validate_python({"domain": "example.com"})
    assert bundle.domain == "example.com"
    assert bundle.status == "NOT_FOUND"
    assert bundle.is_valid is False
    assert bundle.needs_renewal is False
    assert bundle.challenge_type == "http-01"


def test_certificate_bundle_validation_error() -> None:
    with pytest.raises(ValidationError):
        CERTIFICATE_BUNDLE_ADAPTER.validate_python({"domain": ""})


def test_ssl_audit_report_defaults() -> None:
    report = SSL_AUDIT_REPORT_ADAPTER.validate_python({
        "all_valid": True,
        "requires_action": False,
        "audited_at": "2026-11-17T01:00:00Z",
    })
    assert report.all_valid is True
    assert len(report.certificates) == 0
