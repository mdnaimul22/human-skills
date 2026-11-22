from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.helpers import ValidationError

_PROMO_CODE_RE = re.compile(r"^[A-Z0-9_-]{2,32}$")


def _normalize_promo(v: str) -> str:
    clean = v.strip().upper()
    if not _PROMO_CODE_RE.match(clean):
        raise ValidationError("Invalid promo code format")
    return clean


class ClaimRequest(BaseModel):
    code: str = Field(min_length=1, max_length=32)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return _normalize_promo(v)


class ClaimResponse(BaseModel):
    code: str
    credits_granted: int
    available_credits: int
    message: str


class PromoCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    credits: int = Field(gt=0, le=10000)
    max_uses: Optional[int] = Field(default=None, gt=0, le=100000)
    expires_at: Optional[datetime] = None
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return _normalize_promo(v)


class PromoResponse(BaseModel):
    id: str
    code: str
    credits: int
    max_uses: Optional[int]
    current_uses: int
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
