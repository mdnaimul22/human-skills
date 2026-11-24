from __future__ import annotations

from datetime import datetime, timezone
from cryptography import x509
from src.config import Settings, setup_logger, sys_is_file, sys_read_bytes
from src.helpers import ValidationError
from .schema import CertificateBundle, SslAuditReport

logger = setup_logger(Settings.LOG_DIR / "certbot.log", name="apps.certbot.auditor")


class Auditor:
    DEFAULT_CERTS_DIR: str = "/etc/letsencrypt/live"
    RENEWAL_THRESHOLD_DAYS: int = 30

    @classmethod
    def audit(cls, domain: str, certs_dir: str = DEFAULT_CERTS_DIR) -> CertificateBundle:
        norm_domain = domain.strip().lower()
        if not norm_domain:
            raise ValidationError("Domain name must not be empty.")

        cert_dir = f"{certs_dir}/{norm_domain}"
        fullchain = f"{cert_dir}/fullchain.pem"
        cert_file = f"{cert_dir}/cert.pem"
        privkey = f"{cert_dir}/privkey.pem"

        target_cert = fullchain if sys_is_file(fullchain) else (cert_file if sys_is_file(cert_file) else "")
        target_key = privkey if sys_is_file(privkey) else ""

        if not target_cert or not target_key:
            return CertificateBundle(
                domain=norm_domain,
                fullchain_path=target_cert,
                privkey_path=target_key,
                status="NOT_FOUND",
                is_valid=False,
                needs_renewal=True,
                challenge_type="http-01",
            )

        try:
            pem_data = sys_read_bytes(target_cert)
            cert = x509.load_pem_x509_certificate(pem_data)
            expiry_utc = cert.not_valid_after_utc
            now_utc = datetime.now(timezone.utc)
            delta = expiry_utc - now_utc
            days_remaining = delta.days
            expires_at = expiry_utc.isoformat()

            if days_remaining < 0:
                return CertificateBundle(
                    domain=norm_domain,
                    fullchain_path=target_cert,
                    privkey_path=target_key,
                    status="EXPIRED",
                    expires_at=expires_at,
                    days_remaining=days_remaining,
                    is_valid=False,
                    needs_renewal=True,
                    challenge_type="http-01",
                )

            needs_renewal = days_remaining <= cls.RENEWAL_THRESHOLD_DAYS
            status = "EXPIRING_SOON" if needs_renewal else "VALID"

            return CertificateBundle(
                domain=norm_domain,
                fullchain_path=target_cert,
                privkey_path=target_key,
                status=status,
                expires_at=expires_at,
                days_remaining=days_remaining,
                is_valid=True,
                needs_renewal=needs_renewal,
                challenge_type="http-01",
            )
        except Exception as e:
            logger.error(f"Failed to inspect certificate for '{norm_domain}': {e}")
            return CertificateBundle(
                domain=norm_domain,
                fullchain_path=target_cert,
                privkey_path=target_key,
                status="INVALID",
                is_valid=False,
                needs_renewal=True,
                challenge_type="http-01",
            )

    @classmethod
    def audit_all(cls, domains: list[str], certs_dir: str = DEFAULT_CERTS_DIR) -> SslAuditReport:
        bundles = [cls.audit(d, certs_dir=certs_dir) for d in domains]
        all_valid = len(bundles) > 0 and all(b.is_valid and not b.needs_renewal for b in bundles)
        action_domains = [b.domain for b in bundles if b.needs_renewal or not b.is_valid]
        requires_action = len(action_domains) > 0

        return SslAuditReport(
            certificates=bundles,
            all_valid=all_valid,
            requires_action=requires_action,
            action_domains=action_domains,
            audited_at=datetime.now(timezone.utc).isoformat(),
        )
