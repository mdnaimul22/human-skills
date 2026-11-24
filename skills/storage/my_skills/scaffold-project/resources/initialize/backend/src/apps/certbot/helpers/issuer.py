from __future__ import annotations

import re
import subprocess
from typing import Optional
from src.config import Settings, ensure_dir, setup_logger
from src.helpers import ValidationError
from .auditor import Auditor
from .schema import CertificateBundle

logger = setup_logger(Settings.LOG_DIR / "certbot.log", name="apps.certbot.issuer")
_DOMAIN_REGEX = re.compile(r"^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$|^localhost$")


class Issuer:
    DEFAULT_WEBROOT: str = "/var/www/html"
    DEFAULT_CERTS_DIR: str = "/etc/letsencrypt/live"

    @classmethod
    def issue(
        cls,
        domain: str,
        extra_domains: Optional[list[str]] = None,
        email: Optional[str] = None,
        webroot_path: str = DEFAULT_WEBROOT,
        dry_run: bool = False,
        certs_dir: str = DEFAULT_CERTS_DIR,
    ) -> CertificateBundle:
        norm_domain = domain.strip().lower()
        if not norm_domain or not _DOMAIN_REGEX.match(norm_domain):
            raise ValidationError(f"Invalid domain name: '{domain}'.")

        target_email = email.strip() if email and email.strip() else (Settings.SSL_EMAIL.strip() if Settings.SSL_EMAIL else f"admin@{norm_domain}")
        extra_list = [d.strip().lower() for d in (extra_domains or []) if d.strip().lower()]
        for extra in extra_list:
            if not _DOMAIN_REGEX.match(extra):
                raise ValidationError(f"Invalid extra domain name: '{extra}'.")

        ensure_dir(f"{webroot_path}/.well-known/acme-challenge")

        cmd: list[str] = [
            "sudo", "certbot", "certonly",
            "--webroot",
            "-w", webroot_path,
            "--non-interactive",
            "--agree-tos",
            "-m", target_email,
            "-d", norm_domain,
        ]

        for extra in extra_list:
            if extra != norm_domain:
                cmd.extend(["-d", extra])

        if dry_run:
            cmd.append("--dry-run")

        logger.info(f"Executing HTTP-01 webroot ACME challenge for '{norm_domain}' (dry_run={dry_run})...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if res.returncode == 0:
                logger.info(f"Certbot HTTP-01 challenge succeeded for '{norm_domain}'.")
                if dry_run:
                    return CertificateBundle(
                        domain=norm_domain,
                        status="DRY_RUN_SUCCESS",
                        is_valid=True,
                        needs_renewal=False,
                        challenge_type="http-01",
                    )
                return Auditor.audit(norm_domain, certs_dir=certs_dir)

            err_msg = res.stderr.strip() or res.stdout.strip()
            logger.error(f"Certbot HTTP-01 challenge failed for '{norm_domain}': {err_msg}")
            return CertificateBundle(
                domain=norm_domain,
                status="FAILED",
                is_valid=False,
                needs_renewal=True,
                challenge_type="http-01",
            )
        except Exception as e:
            logger.error(f"Exception during Certbot HTTP-01 issuance for '{norm_domain}': {e}")
            return CertificateBundle(
                domain=norm_domain,
                status="FAILED",
                is_valid=False,
                needs_renewal=True,
                challenge_type="http-01",
            )
