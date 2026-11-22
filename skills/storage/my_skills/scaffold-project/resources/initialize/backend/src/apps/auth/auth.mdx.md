# auth.py DOX

> *`src/apps/auth/` acts as the "Universal Platform Identity & Authorization Control Plane":*
> *It is 100% decoupled from application-specific domains (`src/core/`, `src/db/domain/*`).*
> *It manages multi-provider identities, Fernet-encrypted credential vaults, rotating refresh sessions with replay detection, stateless Principal resolution, and scope-based route guards.*

## Purpose

- Own the `src/apps/auth` universal authentication and authorization control plane.
- Separate account records (`User`) from OAuth/login identities (`UserIdentity`) to support multi-provider authentication without schema churn.
- Encrypt third-party provider credentials (`access_token_enc`, `refresh_token_enc`) at rest via deterministic Fernet keys derived from `Settings.JWT_SECRET`.
- Issue short-lived signed JWT access tokens (`TokenClaims`) paired with rotating opaque refresh sessions (`AuthSession`) and automatic replay-detection family revocation.
- Inject immutable `Principal` objects into HTTP routers via FastAPI dependencies (`require_principal`, `optional_principal`, `require_scope`) without leaking mutable ORM entities into domain layers.
- Keep this module-level DOX profile synchronized with `src/apps/auth/` implementation files.

## Ownership

- `src/apps/auth/manager.py` owns the public orchestrator facade (`AuthManager`).
- `src/apps/auth/helpers/` owns internal sub-engine workers (`schema.py`, `tokens.py`, `vault.py`, `oauth.py`, `guards.py`).
- **Classes:**
  - `AuthManager` (Public Facade / Orchestrator)
    - `get_google_login_url(self, redirect_uri: str | None = None) -> str`
    - `async login_with_google(self, code: str, session: AsyncSession, user_agent: str = "") -> AuthSessionBundle`
    - `async refresh_session(self, raw_refresh_token: str, session: AsyncSession) -> AuthSessionBundle`
    - `async revoke_token(self, token: str, session: AsyncSession) -> None`
    - `async revoke_session(self, session_id: str, session: AsyncSession) -> None`
    - `async provider_credential(self, user_id: str, provider: str, session: AsyncSession, auto_refresh: bool = True) -> ProviderCredential | None`
    - `get_auth_manager() -> AuthManager`
  - `GoogleOAuthClient` (`helpers/oauth.py`)
    - `get_auth_url(self, redirect_uri: str | None, state: str | None) -> str`
    - `async exchange_code(self, code: str, redirect_uri: str | None) -> GoogleTokenPayload`
    - `async refresh_access_token(self, refresh_token: str) -> GoogleRefreshPayload`
  - `Principal` (`helpers/schema.py`)
    - Frozen, immutable request principal: `user_id`, `id`, `tier`, `scopes`, `jti`, `email`, `name`, `avatar_url`, `access_token`.
  - `TokenClaims` (`helpers/schema.py`)
    - Frozen JWT claims representation: `sub`, `tier`, `typ`, `jti`, `iat`, `exp`, `scopes`.
  - `ProviderCredential` (`helpers/schema.py`)
    - Provider credential model: `provider`, `subject`, `access_token`, `expires_at`.
  - `AuthSessionBundle` (`helpers/schema.py`)
    - Full session payload: `token`, `access_token`, `refresh_token`, `session_id`, `user_id`, `name`, `email`, `avatar_url`, `tier`.
- **Top-level Functions:**
  - `create_token(user_id: str, tier: str, expires_in_seconds: int, token_type: str, scopes: Sequence[str]) -> str`
  - `decode_token_claims(token: str, expected_type: str | None) -> TokenClaims`
  - `decode_token(token: str, expected_type: str | None) -> str`
  - `issue_refresh_token(session_id: str) -> tuple[str, str]`
  - `parse_refresh_token(raw_token: str) -> tuple[str, str]`
  - `hash_password(password: str) -> str`
  - `verify_password(password: str, stored_hash: str) -> bool`
  - `encrypt_secret(plaintext: str | None) -> str | None`
  - `decrypt_secret(ciphertext: str | None) -> str | None`
  - `issue_oauth_state() -> str`
  - `verify_oauth_state(state: str | None, max_age_seconds: int) -> bool`
  - `require_principal(request, authorization, session) -> Principal`
  - `optional_principal(request, authorization, session) -> Principal | None`
  - `require_scope(required_scope: str) -> Callable`
  - `get_current_user` (alias to `require_principal`)
  - `get_optional_user` (alias to `optional_principal`)

## Runtime Contracts

- **Singleton Pattern:** External callers instantiate `AuthManager` or call `get_auth_manager()`.
- **Stateless Access Verification:** Routes verify access via signed HMAC-SHA256 JWT tokens with automatic revocation blacklist lookup (`RevokedTokenRepository`).
- **Cryptographic State Defense:** OAuth state tokens embed timestamp, nonce, and HMAC-SHA256 signature to eliminate CSRF and authorization code injection.
- **Fail-Fast Credential Vault:** Decryption of tampered or invalid Fernet ciphertext fails fast and returns `None` rather than falling back to corrupted data.
- **Session Replay Protection:** Re-presenting an already consumed or invalid refresh token triggers automatic revocation of all active sessions for that user.

## Key Concepts

- **Identity vs User Separation:**
  - `User` entity holds core profile data, tier, and activity metrics.
  - `UserIdentity` holds third-party provider accounts (Google, local, future SAML/OIDC) linked via `user_id`.
- **Vault At Rest:**
  - Sensitive third-party tokens are never stored in plaintext in the database.
  - Encryption uses Fernet derived from `Settings.JWT_SECRET`.
- **Token Family Invalidation:**
  - When refreshing a session, a new refresh token is issued while the previous one is marked rotated.
  - If a leaked/old refresh token is presented again, the system recognizes an active replay attack and immediately revokes all family sessions.

## Work Guidance

- Never perform blocking network calls (`requests.get`, `httpx.Client()`) inside authentication pathways.
- Keep `Principal` and `TokenClaims` immutable (`frozen=True`) to avoid accidental state pollution across async handlers.
- Preserve zero-comment and zero-docstring clean code rules inside Python implementations.

## Verification

- Run AST architecture compliance linter:
  ```bash
  human-skills '{"tool_name": "linter", "tool_args": {"scan_path": "src/apps/auth"}}'
  ```
- Run targeted authentication test suite:
  ```bash
  PYTHONPATH=. pytest tests/apps/auth/ -v --durations=0
  ```

## Child DOX Index

- [helpers/guards.py](helpers/guards.py)
- [helpers/oauth.py](helpers/oauth.py)
- [helpers/schema.py](helpers/schema.py)
- [helpers/tokens.py](helpers/tokens.py)
- [helpers/vault.py](helpers/vault.py)
