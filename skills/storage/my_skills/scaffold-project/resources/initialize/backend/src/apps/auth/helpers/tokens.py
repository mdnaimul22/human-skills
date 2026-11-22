from __future__ import annotations
from datetime import timedelta
import hashlib
import hmac
import secrets
from typing import Sequence
import uuid
import jwt
from src.apps.auth.helpers.schema import TokenClaims
from src.config import Settings
from src.helpers import AuthenticationError, ValidationError, get_now_utc

TokenPayload = str

def create_token(
    user_id: str,
    tier: str = "registered",
    expires_in_seconds: int = 86400,
    token_type: str = "access",
    scopes: Sequence[str] = (),
) -> str:
    now = get_now_utc()
    jti = uuid.uuid4().hex
    payload = {
        "sub": user_id,
        "tier": tier,
        "typ": token_type,
        "jti": jti,
        "scopes": list(scopes),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
    }
    return jwt.encode(payload, Settings.JWT_SECRET, algorithm="HS256")

def decode_token_claims(token: str, expected_type: str | None = None) -> TokenClaims:
    try:
        raw = jwt.decode(token, Settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid token") from exc
    user_id = raw.get("sub")
    if not user_id:
        raise ValidationError("Invalid token: missing subject")
    raw_scopes = raw.get("scopes") or ()
    claims = TokenClaims(
        sub=str(user_id),
        tier=str(raw.get("tier") or "registered"),
        typ=str(raw.get("typ") or "access"),
        jti=str(raw.get("jti") or ""),
        iat=int(raw.get("iat") or 0),
        exp=int(raw.get("exp") or 0),
        scopes=tuple(str(s) for s in raw_scopes),
    )
    if expected_type is not None and claims.typ != expected_type:
        raise AuthenticationError(f"Invalid token type: expected {expected_type}")
    return claims

def decode_token(token: str, expected_type: str | None = None) -> str:
    claims = decode_token_claims(token, expected_type=expected_type)
    return claims.sub

def issue_refresh_token(session_id: str) -> tuple[str, str]:
    secret_part = secrets.token_urlsafe(32)
    raw_token = f"{session_id}.{secret_part}"
    digest = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, digest

def parse_refresh_token(raw_token: str) -> tuple[str, str]:
    if not raw_token or "." not in raw_token:
        raise AuthenticationError("Malformed refresh token")
    session_id, secret_part = raw_token.split(".", 1)
    if not session_id or not secret_part:
        raise AuthenticationError("Malformed refresh token")
    digest = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return session_id, digest

def hash_password(password: str) -> str:
    if not password or len(password) < 6:
        raise ValidationError("Password must be at least 6 characters")
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"pbkdf2_sha256$200000${salt}${dk.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        parts = stored_hash.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_hex = parts[3]
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(dk.hex(), expected_hex)
    except (ValueError, TypeError):
        return False
