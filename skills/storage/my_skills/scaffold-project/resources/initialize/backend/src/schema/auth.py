from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.helpers import ValidationError


class RegisterRequest(BaseModel):
    email: str
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValidationError("Invalid email address")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=1)


class GoogleAuthUrlResponse(BaseModel):
    url: str


class GoogleCallbackRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    token: str
    user_id: str
    name: str
    email: str
    avatar_url: Optional[str] = None
    tier: Optional[str] = "registered"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class RegisterResponse(BaseModel):
    message: str
    email: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    name: str
    email: str


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    tier: str = "registered"
    email_verified: bool = True
    auth_method: str = "oauth"
    created_at: datetime
    total_downloads: int = 0
    total_favorites: int = 0


class GoogleUserInfo(BaseModel):
    google_id: str
    email: str
    name: str
    email_verified: bool
