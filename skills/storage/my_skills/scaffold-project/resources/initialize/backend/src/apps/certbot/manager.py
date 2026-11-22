from __future__ import annotations

import threading
from typing import Optional
from src.config import Settings, setup_logger
from .helpers import (
    Auditor,
    CertificateBundle,
    Issuer,
    SslAuditReport,
)

logger = setup_logger(Settings.LOG_DIR / "certbot.log", name="apps.certbot.manager")


class CertbotManager:
    _instance: Optional[CertbotManager] = None
    _initialized: bool = False

    def __new__(cls) -> CertbotManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._lock = threading.Lock()
        self._initialized = True
        logger.info("CertbotManager initialized successfully.")

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None
        cls._initialized = False

    def get_certificate(self, domain: str) -> CertificateBundle:
        with self._lock:
            return Auditor.audit(domain)

    def ensure_certificate(
        self,
        domain: str,
        extra_domains: Optional[list[str]] = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> CertificateBundle:
        with self._lock:
            existing = Auditor.audit(domain)
            if existing.is_valid and not existing.needs_renewal and not force:
                logger.info(
                    f"Certificate for '{domain}' is active ({existing.days_remaining}d remaining). Skipping issuance."
                )
                return existing

            logger.info(f"Certificate for '{domain}' requires issuance (status={existing.status}). Running challenge...")
            return Issuer.issue(
                domain=domain,
                extra_domains=extra_domains,
                dry_run=dry_run,
            )

    def audit_all(self, domains: list[str]) -> SslAuditReport:
        with self._lock:
            return Auditor.audit_all(domains)

    def is_ssl_active(self, domain: str) -> bool:
        bundle = self.get_certificate(domain)
        return bundle.is_valid


def get_certbot_manager() -> CertbotManager:
    return CertbotManager()
