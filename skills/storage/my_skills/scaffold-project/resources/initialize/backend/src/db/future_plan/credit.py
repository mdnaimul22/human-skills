from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

TransactionType = Literal["grant", "deduct", "reserve", "commit", "refund"]
CreditOperation = Literal["will_be_assigne_when needed"]


class Balance(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    available: int = Field(..., ge=0)
    reserved: int = Field(..., ge=0)
    total: int = Field(..., ge=0)
    updated_at: datetime


class ReservationRequest(BaseModel):
    operation: CreditOperation
    amount: int = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=16, pattern=r"^[a-zA-Z0-9_-]+$")
    reference_id: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")


class ReservationResponse(BaseModel):
    reservation_id: str = Field(..., pattern=r"^res_[a-zA-Z0-9_-]+$")
    user_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    amount: int = Field(..., gt=0)
    status: Literal["reserved", "committed", "refunded"]
    remaining_available: int = Field(..., ge=0)


class CommitRequest(BaseModel):
    reservation_id: str = Field(..., pattern=r"^res_[a-zA-Z0-9_-]+$")
    idempotency_key: str = Field(..., min_length=16, pattern=r"^[a-zA-Z0-9_-]+$")


class RefundRequest(BaseModel):
    reservation_id: str = Field(..., pattern=r"^res_[a-zA-Z0-9_-]+$")
    reason: str = Field(..., min_length=3)


class DeductRequest(BaseModel):
    operation: CreditOperation
    amount: int = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=16, pattern=r"^[a-zA-Z0-9_-]+$")
    reference_id: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")


class LedgerEntry(BaseModel):
    id: str = Field(..., pattern=r"^tx_[a-zA-Z0-9_-]+$")
    user_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    transaction_type: TransactionType
    amount: int
    balance_after: int = Field(..., ge=0)
    reservation_id: Optional[str] = None
    idempotency_key: str = Field(..., min_length=16)
    reference_id: Optional[str] = None
    operation: Optional[CreditOperation] = None
    description: str = Field(default="")
    created_at: datetime


class CostPolicy(BaseModel):
    operation: CreditOperation
    cost: int = Field(..., ge=1)
    is_active: bool = True


class QuotaResponse(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    tier: str
    daily_limit: int = Field(..., ge=0)
    daily_used: int = Field(..., ge=0)
    monthly_limit: int = Field(..., ge=0)
    monthly_used: int = Field(..., ge=0)
    balance: CreditBalance
