from __future__ import annotations
from .guards import (
    get_current_user, get_optional_user,
    optional_principal, require_principal, require_scope,
)
from .oauth import (
    GoogleOAuthClient, GoogleRefreshPayload, GoogleTokenPayload,
    exchange_google_code, exchange_google_code_async, get_google_auth_url,
    issue_oauth_state, refresh_google_access_token, refresh_google_access_token_async,
    verify_oauth_state,
)
from .schema import AuthSessionBundle, Principal, ProviderCredential, TokenClaims
from .tokens import (
    TokenPayload, create_token, decode_token, decode_token_claims,
    hash_password, issue_refresh_token, parse_refresh_token, verify_password,
)
from .vault import decrypt_secret, encrypt_secret

__all__ = [
    "AuthSessionBundle", "GoogleOAuthClient", "GoogleRefreshPayload",
    "GoogleTokenPayload", "Principal", "ProviderCredential", "TokenClaims", "TokenPayload",
    "create_token", "decode_token", "decode_token_claims",
    "decrypt_secret", "encrypt_secret", "exchange_google_code", "exchange_google_code_async",
    "get_current_user", "get_google_auth_url", "get_optional_user", "hash_password",
    "issue_oauth_state", "issue_refresh_token", "optional_principal", "parse_refresh_token",
    "refresh_google_access_token", "refresh_google_access_token_async",
    "require_principal", "require_scope", "verify_oauth_state", "verify_password",
]
