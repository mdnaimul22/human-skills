from __future__ import annotations
import hashlib
import hmac
import secrets
import time
from typing import TypedDict
import urllib.parse
import httpx
from src.config import Settings
from src.helpers import ValidationError

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

class GoogleTokenPayload(TypedDict, total=False):
    google_id: str | None
    email: str | None
    name: str | None
    avatar_url: str | None
    access_token: str | None
    refresh_token: str | None
    expires_in: int

class GoogleRefreshPayload(TypedDict, total=False):
    access_token: str | None
    expires_in: int

def _sign_state_payload(payload: str) -> str:
    secret = Settings.JWT_SECRET.encode("utf-8")
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

def issue_oauth_state() -> str:
    ts = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    payload = f"{ts}.{nonce}"
    sig = _sign_state_payload(payload)
    return f"{payload}.{sig}"

def verify_oauth_state(state: str | None, max_age_seconds: int = 600) -> bool:
    if not state:
        return False
    parts = state.split(".")
    if len(parts) != 3:
        return False
    ts_str, nonce, sig = parts
    if not ts_str.isdigit() or not nonce or not sig:
        return False
    payload = f"{ts_str}.{nonce}"
    expected_sig = _sign_state_payload(payload)
    if not hmac.compare_digest(sig, expected_sig):
        return False
    age = int(time.time()) - int(ts_str)
    return -30 <= age <= max_age_seconds

def _code_payload(code: str, redirect_uri: str | None = None) -> dict[str, str]:
    return {
        "code": code,
        "client_id": Settings.GOOGLE_CLIENT_ID,
        "client_secret": Settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri or Settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

def _refresh_payload(refresh_token: str) -> dict[str, str]:
    return {
        "client_id": Settings.GOOGLE_CLIENT_ID,
        "client_secret": Settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

def _format_user_payload(
    token_data: dict[str, str | int | None],
    user_data: dict[str, str | None],
) -> GoogleTokenPayload:
    raw_email = str(user_data.get("email") or "")
    raw_name = str(user_data.get("name") or (raw_email.split("@")[0] if raw_email else ""))
    exp_val = token_data.get("expires_in")
    return {
        "google_id": user_data.get("sub"),
        "email": user_data.get("email"),
        "name": raw_name,
        "avatar_url": user_data.get("picture"),
        "access_token": str(token_data["access_token"]) if token_data.get("access_token") else None,
        "refresh_token": str(token_data["refresh_token"]) if token_data.get("refresh_token") else None,
        "expires_in": int(exp_val) if exp_val is not None else 3600,
    }

class GoogleOAuthClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def get_auth_url(self, redirect_uri: str | None = None, state: str | None = None) -> str:
        params = {
            "client_id": Settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri or Settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state or issue_oauth_state(),
        }
        return f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str | None = None) -> GoogleTokenPayload:
        payload = _code_payload(code, redirect_uri)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(_GOOGLE_TOKEN_URL, data=payload)
                token_data = resp.json()
                access_token = token_data.get("access_token")
                headers = {"Authorization": f"Bearer {access_token}"}
                user_resp = await client.get(_GOOGLE_USERINFO_URL, headers=headers)
                user_data = user_resp.json()
        except Exception as exc:
            raise ValidationError(f"Failed to exchange Google OAuth code: {exc}") from exc
        return _format_user_payload(token_data, user_data)

    async def refresh_access_token(self, refresh_token: str) -> GoogleRefreshPayload:
        payload = _refresh_payload(refresh_token)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(_GOOGLE_TOKEN_URL, data=payload)
                token_data = resp.json()
                return {
                    "access_token": token_data.get("access_token"),
                    "expires_in": int(token_data.get("expires_in", 3600)),
                }
        except Exception as exc:
            raise ValidationError(f"Failed to refresh Google access token: {exc}") from exc

_default_client = GoogleOAuthClient()

def get_google_auth_url(redirect_uri: str | None = None, state: str | None = None) -> str:
    return _default_client.get_auth_url(redirect_uri, state=state)

async def exchange_google_code(code: str, redirect_uri: str | None = None) -> GoogleTokenPayload:
    return await _default_client.exchange_code(code, redirect_uri)

async def refresh_google_access_token(refresh_token: str) -> GoogleRefreshPayload:
    return await _default_client.refresh_access_token(refresh_token)

exchange_google_code_async = exchange_google_code
refresh_google_access_token_async = refresh_google_access_token
