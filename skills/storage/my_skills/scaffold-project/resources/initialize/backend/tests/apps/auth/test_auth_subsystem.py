from __future__ import annotations
from datetime import timedelta
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.apps.auth import (
    AuthManager, Principal, create_token, decode_token, decode_token_claims,
    decrypt_secret, encrypt_secret, hash_password, optional_principal,
    require_principal, require_scope, verify_password,
)
from src.db import Base, IdentityRepository, UserRepository, system_table_names
from src.helpers import AuthenticationError, PermissionDeniedError, ValidationError, get_now_utc

@pytest_asyncio.fixture
async def auth_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sys_names = system_table_names()
    sys_tables = [t for name, t in Base.metadata.tables.items() if name in sys_names]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=sys_tables))
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()

def test_vault_encryption_and_idempotency():
    raw = "ya29.a0AfH6SMBx_secret_google_token"
    enc = encrypt_secret(raw)
    assert enc is not None
    assert enc != raw
    assert encrypt_secret(enc) == enc
    assert decrypt_secret(enc) == raw
    assert decrypt_secret("invalid_or_non_fernet_token") is None
    assert encrypt_secret(None) is None
    assert decrypt_secret(None) is None

def test_tokens_and_password_hashing():
    tok = create_token("usr_1", tier="premium", scopes=("cv:write", "cv:read"))
    assert str(decode_token(tok)) == "usr_1"
    claims = decode_token_claims(tok)
    assert claims.sub == "usr_1"
    assert claims.tier == "premium"
    assert claims.typ == "access"
    assert "cv:write" in claims.scopes
    assert len(claims.jti) == 32

    verify_tok = create_token("usr_1", token_type="verify_email")
    assert str(decode_token(verify_tok, "verify_email")) == "usr_1"
    with pytest.raises(AuthenticationError):
        decode_token(verify_tok, "reset_password")

    pw_hash = hash_password("SuperSecret123!")
    assert verify_password("SuperSecret123!", pw_hash) is True
    assert verify_password("WrongPass999", pw_hash) is False

@pytest.mark.asyncio
async def test_auth_manager_login_refresh_replay_and_revocation(
    auth_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_exchange(code: str, redirect_uri: str | None = None):
        return {
            "google_id": "g_sub_999", "email": "architect@example.com",
            "name": "System Architect", "avatar_url": "https://example.com/a.png",
            "access_token": "goog_at_initial", "refresh_token": "goog_rt_initial",
            "expires_in": 3600,
        }

    monkeypatch.setattr("src.apps.auth.manager.exchange_google_code_async", _fake_exchange)
    mgr = AuthManager()

    bundle = await mgr.login_with_google("valid_code", auth_session, user_agent="pytest")
    assert bundle.email == "architect@example.com"
    assert bundle.refresh_token.startswith(f"{bundle.session_id}.")

    ident = await IdentityRepository(auth_session).find("google", "g_sub_999")
    assert ident is not None
    assert ident.access_token_enc != "goog_at_initial"
    assert decrypt_secret(ident.access_token_enc) == "goog_at_initial"

    principal = await require_principal(
        request=None, authorization=f"Bearer {bundle.access_token}", session=auth_session,
    )
    assert type(principal) is Principal
    assert principal.user_id == bundle.user_id
    assert principal.id == bundle.user_id
    assert principal.access_token == "goog_at_initial"

    rotated = await mgr.refresh_session(bundle.refresh_token, auth_session)
    assert rotated.session_id == bundle.session_id
    assert rotated.refresh_token != bundle.refresh_token

    with pytest.raises(AuthenticationError):
        await mgr.refresh_session(bundle.refresh_token, auth_session)

    with pytest.raises(AuthenticationError):
        await mgr.refresh_session(rotated.refresh_token, auth_session)

    await mgr.revoke_token(bundle.access_token, auth_session)
    with pytest.raises(AuthenticationError):
        await require_principal(
            request=None, authorization=f"Bearer {bundle.access_token}", session=auth_session,
        )

    opt = await optional_principal(
        request=None, authorization=f"Bearer {bundle.access_token}", session=auth_session,
    )
    assert opt is None

@pytest.mark.asyncio
async def test_provider_credential_auto_refresh_and_scopes(
    auth_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    user_repo = UserRepository(auth_session)
    expired_at = get_now_utc() - timedelta(minutes=10)
    user, _ = await user_repo.upsert_oauth_user(
        provider="google", subject="g_sub_refresh", email="refresh@example.com",
        name="Refresh User", access_token_enc=encrypt_secret("old_goog_at"),
        refresh_token_enc=encrypt_secret("valid_goog_rt"), token_expires_at=expired_at,
    )

    async def _fake_refresh(refresh_token: str):
        assert refresh_token == "valid_goog_rt"
        return {"access_token": "fresh_goog_at_2026", "expires_in": 3600}

    monkeypatch.setattr("src.apps.auth.manager.refresh_google_access_token_async", _fake_refresh)
    cred = await AuthManager().provider_credential(user.id, "google", auth_session, auto_refresh=True)
    assert cred is not None
    assert cred.access_token == "fresh_goog_at_2026"

    scoped_principal = Principal(user_id=user.id, id=user.id, scopes=frozenset({"cv:read"}))
    read_guard = require_scope("cv:read")
    write_guard = require_scope("cv:write")
    assert (await read_guard(scoped_principal)).user_id == user.id
    with pytest.raises(PermissionDeniedError):
        await write_guard(scoped_principal)

@pytest.mark.asyncio
async def test_unified_services_apps_auth_lifecycle(auth_session: AsyncSession):
    from src.services.apps import auth as auth_svc

    reg = await auth_svc.register(
        email="NewUser@Example.com", name="New User",
        password="InitialPassword123!", session=auth_session, referral_code="REF2026",
    )
    assert reg["email"] == "newuser@example.com"

    verified = await auth_svc.verify_email(reg["verification_token"], auth_session)
    assert verified["user_id"] == reg["user_id"]

    logged_in = await auth_svc.login("newuser@example.com", "InitialPassword123!", auth_session)
    assert logged_in["email"] == "newuser@example.com"

    refreshed = await auth_svc.refresh_tokens(logged_in["refresh_token"], auth_session)
    assert refreshed["user_id"] == reg["user_id"]
    with pytest.raises(AuthenticationError):
        await auth_svc.refresh_tokens(logged_in["refresh_token"], auth_session)

    await auth_svc.change_password(
        reg["user_id"], "InitialPassword123!", "UpdatedPassword456!", auth_session,
    )
    with pytest.raises(AuthenticationError):
        await auth_svc.login("newuser@example.com", "InitialPassword123!", auth_session)
    re_login = await auth_svc.login("newuser@example.com", "UpdatedPassword456!", auth_session)
    assert re_login["user_id"] == reg["user_id"]

    reset_tok = await auth_svc.request_password_reset("newuser@example.com", auth_session)
    assert reset_tok is not None
    await auth_svc.reset_password(reset_tok, "ResetPassword789!", auth_session)
    after_reset = await auth_svc.login("newuser@example.com", "ResetPassword789!", auth_session)
    assert after_reset["user_id"] == reg["user_id"]

    updated_prof = await auth_svc.update_profile(reg["user_id"], "Renamed User", auth_session)
    assert updated_prof["name"] == "Renamed User"

    await auth_svc.logout(after_reset["refresh_token"], reg["user_id"], auth_session)
    with pytest.raises(AuthenticationError):
        await auth_svc.refresh_tokens(after_reset["refresh_token"], auth_session)


def test_oauth_state_generation_verification_and_callback_csrf_defense(auth_session: AsyncSession):
    from urllib.parse import parse_qs, urlparse
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.apps.auth import get_google_auth_url, issue_oauth_state, verify_oauth_state
    from src.db import get_session
    from src.routers.apps.auth import router as auth_router

    state = issue_oauth_state()
    assert verify_oauth_state(state) is True
    assert verify_oauth_state(None) is False
    assert verify_oauth_state("") is False
    assert verify_oauth_state("invalid.state") is False
    assert verify_oauth_state(state + "tampered") is False
    assert verify_oauth_state(state, max_age_seconds=-100) is False

    url = get_google_auth_url()
    qs = parse_qs(urlparse(url).query)
    assert "state" in qs
    assert verify_oauth_state(qs["state"][0]) is True

    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_session] = lambda: auth_session
    client = TestClient(app, base_url="http://localhost:8000")

    r_no_state = client.get("/api/v1/auth/callback?code=fake_code", follow_redirects=False)
    assert r_no_state.status_code == 307
    assert "error=invalid_state" in r_no_state.headers["location"]

    r_bad_state = client.get("/api/v1/auth/callback?code=fake_code&state=123.abc.bad", follow_redirects=False)
    assert r_bad_state.status_code == 307
    assert "error=invalid_state" in r_bad_state.headers["location"]
