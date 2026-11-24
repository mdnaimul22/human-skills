from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from src.helpers import ValidationError
from src.apps.certbot.helpers.auditor import Auditor
from src.apps.certbot.helpers.schema import CertificateBundle, SslAuditReport


def _create_test_pki(target_dir: str, days_valid: int) -> None:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    if days_valid < 0:
        not_before = now + timedelta(days=days_valid - 5)
        not_after = now + timedelta(days=days_valid)
    else:
        not_before = now - timedelta(days=1)
        not_after = now + timedelta(days=days_valid)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "example.com"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .sign(key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    (target / "fullchain.pem").write_bytes(cert_pem)
    (target / "privkey.pem").write_bytes(key_pem)


def test_audit_empty_domain() -> None:
    with pytest.raises(ValidationError):
        Auditor.audit("   ")


def test_audit_missing_certificate(tmp_path: pytest.TempPathFactory) -> None:
    bundle = Auditor.audit("nonexistent.xyz", certs_dir=str(tmp_path))
    assert bundle.status == "NOT_FOUND"
    assert bundle.is_valid is False
    assert bundle.needs_renewal is True


def test_audit_valid_certificate(tmp_path: pytest.TempPathFactory) -> None:
    domain = "example.com"
    cert_dir = f"{tmp_path}/{domain}"
    _create_test_pki(cert_dir, days_valid=75)

    bundle = Auditor.audit(domain, certs_dir=str(tmp_path))
    assert bundle.domain == domain
    assert bundle.status == "VALID"
    assert bundle.is_valid is True
    assert bundle.needs_renewal is False
    assert bundle.days_remaining is not None and bundle.days_remaining > 30


def test_audit_expiring_soon_certificate(tmp_path: pytest.TempPathFactory) -> None:
    domain = "expiring.xyz"
    cert_dir = f"{tmp_path}/{domain}"
    _create_test_pki(cert_dir, days_valid=15)

    bundle = Auditor.audit(domain, certs_dir=str(tmp_path))
    assert bundle.domain == domain
    assert bundle.status == "EXPIRING_SOON"
    assert bundle.is_valid is True
    assert bundle.needs_renewal is True
    assert bundle.days_remaining is not None and bundle.days_remaining <= 30


def test_audit_expired_certificate(tmp_path: pytest.TempPathFactory) -> None:
    domain = "expired.xyz"
    cert_dir = f"{tmp_path}/{domain}"
    _create_test_pki(cert_dir, days_valid=-2)

    bundle = Auditor.audit(domain, certs_dir=str(tmp_path))
    assert bundle.domain == domain
    assert bundle.status == "EXPIRED"
    assert bundle.is_valid is False
    assert bundle.needs_renewal is True
    assert bundle.days_remaining is not None and bundle.days_remaining < 0


def test_audit_corrupted_certificate(tmp_path: pytest.TempPathFactory) -> None:
    domain = "corrupt.xyz"
    cert_dir = Path(f"{tmp_path}/{domain}")
    cert_dir.mkdir(parents=True, exist_ok=True)
    (cert_dir / "fullchain.pem").write_text("CORRUPTED CERT DATA", encoding="utf-8")
    (cert_dir / "privkey.pem").write_text("CORRUPTED KEY DATA", encoding="utf-8")

    bundle = Auditor.audit(domain, certs_dir=str(tmp_path))
    assert bundle.status == "INVALID"
    assert bundle.is_valid is False
    assert bundle.needs_renewal is True


def test_audit_all_scenarios(tmp_path: pytest.TempPathFactory) -> None:
    _create_test_pki(f"{tmp_path}/valid.xyz", days_valid=80)
    _create_test_pki(f"{tmp_path}/soon.xyz", days_valid=20)

    report = Auditor.audit_all(["valid.xyz", "soon.xyz", "missing.xyz"], certs_dir=str(tmp_path))
    assert isinstance(report, SslAuditReport)
    assert report.all_valid is False
    assert report.requires_action is True
    assert "soon.xyz" in report.action_domains
    assert "missing.xyz" in report.action_domains
    assert "valid.xyz" not in report.action_domains
