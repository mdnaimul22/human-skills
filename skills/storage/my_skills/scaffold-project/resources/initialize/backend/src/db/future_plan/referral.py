from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from src.helpers import ValidationError

_REFERRAL_CODE_RE = re.compile(r"^[A-Z0-9_-]{4,32}$")


class ClaimRequest(BaseModel):
    referral_code: str = Field(min_length=1, max_length=32)
    verification_token: Optional[str] = None

    @field_validator("referral_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        clean = v.strip().upper()
        if not _REFERRAL_CODE_RE.match(clean):
            raise ValidationError("Invalid referral code format")
        return clean


class ClaimResponse(BaseModel):
    referrer_id: str
    referee_id: str
    credits_granted: int
    available_credits: int
    claimed_at: datetime


class StatsResponse(BaseModel):
    referral_code: str
    total_referrals: int
    total_credits_earned: int
