from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class CertificateBundle(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    domain: str = Field(..., min_length=1)
    fullchain_path: str = Field(default="")
    privkey_path: str = Field(default="")
    status: str = Field(default="NOT_FOUND")
    expires_at: Optional[str] = None
    days_remaining: Optional[int] = None
    is_valid: bool = False
    needs_renewal: bool = False
    challenge_type: str = Field(default="http-01")


class SslAuditReport(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    certificates: list[CertificateBundle] = Field(default_factory=list)
    all_valid: bool = False
    requires_action: bool = False
    action_domains: list[str] = Field(default_factory=list)
    audited_at: str = ""


CERTIFICATE_BUNDLE_ADAPTER: TypeAdapter[CertificateBundle] = TypeAdapter(CertificateBundle)
SSL_AUDIT_REPORT_ADAPTER: TypeAdapter[SslAuditReport] = TypeAdapter(SslAuditReport)
