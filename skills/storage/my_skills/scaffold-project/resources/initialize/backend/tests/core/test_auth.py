import asyncio
import time

import pytest

from src.core.auth import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
    decode_token_payload,
    TokenPurpose,
)
from src.helpers import ValidationError, AuthenticationError


class TestHashPassword:
    @pytest.mark.asyncio
    async def test_produces_bcrypt_hash(self):
        hashed = await hash_password("testPassword123")
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    @pytest.mark.asyncio
    async def test_same_password_different_hashes(self):
        h1 = await hash_password("samePassword")
        h2 = await hash_password("samePassword")
        assert h1 != h2

    @pytest.mark.asyncio
    async def test_rejects_password_exceeding_72_bytes(self):
        long_password = "a" * 73
        with pytest.raises(ValidationError, match="72 bytes"):
            await hash_password(long_password)

    @pytest.mark.asyncio
    async def test_accepts_password_at_72_byte_limit(self):
        password_72 = "a" * 72
        hashed = await hash_password(password_72)
        assert hashed.startswith("$2b$")


class TestVerifyPassword:
    @pytest.mark.asyncio
    async def test_correct_password_returns_true(self):
        hashed = await hash_password("correctPassword")
        result = await verify_password("correctPassword", hashed)
        assert result is True

    @pytest.mark.asyncio
    async def test_wrong_password_returns_false(self):
        hashed = await hash_password("correctPassword")
        result = await verify_password("wrongPassword", hashed)
        assert result is False

    @pytest.mark.asyncio
    async def test_malformed_hash_returns_false(self):
        result = await verify_password("anyPassword", "not-a-valid-hash")
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_hash_returns_false(self):
        result = await verify_password("anyPassword", "")
        assert result is False


class TestCreateToken:
    def test_creates_access_token(self):
        token = create_token("user_abc", "access")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_creates_refresh_token(self):
        token = create_token("user_abc", "refresh")
        assert isinstance(token, str)

    def test_creates_verify_email_token(self):
        token = create_token("user_abc", "verify_email")
        assert isinstance(token, str)

    def test_creates_reset_password_token(self):
        token = create_token("user_abc", "reset_password")
        assert isinstance(token, str)

    def test_includes_purpose_claim(self):
        token = create_token("user_abc", "access")
        payload = decode_token_payload(token, "access")
        assert payload["purpose"] == "access"

    def test_includes_subject_claim(self):
        token = create_token("user_abc", "access")
        payload = decode_token_payload(token, "access")
        assert payload["sub"] == "user_abc"

    def test_includes_iat_and_exp_claims(self):
        token = create_token("user_abc", "access")
        payload = decode_token_payload(token, "access")
        assert "iat" in payload
        assert "exp" in payload
        assert payload["exp"] > payload["iat"]

    def test_extra_claims_included(self):
        token = create_token("user_abc", "access", extra_claims={"role": "admin"})
        payload = decode_token_payload(token, "access")
        assert payload["role"] == "admin"

    def test_different_purposes_produce_different_tokens(self):
        t1 = create_token("user_abc", "access")
        t2 = create_token("user_abc", "refresh")
        assert t1 != t2


class TestDecodeToken:
    def test_decodes_valid_access_token(self):
        token = create_token("user_123", "access")
        user_id = decode_token(token, "access")
        assert user_id == "user_123"

    def test_decodes_valid_refresh_token(self):
        token = create_token("user_123", "refresh")
        user_id = decode_token(token, "refresh")
        assert user_id == "user_123"

    def test_decodes_valid_verify_email_token(self):
        token = create_token("user_123", "verify_email")
        user_id = decode_token(token, "verify_email")
        assert user_id == "user_123"

    def test_decodes_valid_reset_password_token(self):
        token = create_token("user_123", "reset_password")
        user_id = decode_token(token, "reset_password")
        assert user_id == "user_123"

    def test_rejects_wrong_purpose_access_as_refresh(self):
        token = create_token("user_123", "access")
        with pytest.raises(AuthenticationError, match="expected refresh"):
            decode_token(token, "refresh")

    def test_rejects_wrong_purpose_refresh_as_access(self):
        token = create_token("user_123", "refresh")
        with pytest.raises(AuthenticationError, match="expected access"):
            decode_token(token, "access")

    def test_rejects_wrong_purpose_verify_as_reset(self):
        token = create_token("user_123", "verify_email")
        with pytest.raises(AuthenticationError, match="expected reset_password"):
            decode_token(token, "reset_password")

    def test_rejects_wrong_purpose_reset_as_verify(self):
        token = create_token("user_123", "reset_password")
        with pytest.raises(AuthenticationError, match="expected verify_email"):
            decode_token(token, "verify_email")

    def test_rejects_invalid_token_string(self):
        with pytest.raises(AuthenticationError, match="Invalid token"):
            decode_token("not.a.valid.jwt", "access")

    def test_rejects_empty_token(self):
        with pytest.raises(AuthenticationError):
            decode_token("", "access")

    def test_rejects_tampered_token(self):
        token = create_token("user_123", "access")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(AuthenticationError):
            decode_token(tampered, "access")


class TestDecodeTokenPayload:
    def test_returns_full_payload_dict(self):
        token = create_token("user_xyz", "access", extra_claims={"tier": "premium"})
        payload = decode_token_payload(token, "access")
        assert isinstance(payload, dict)
        assert payload["sub"] == "user_xyz"
        assert payload["purpose"] == "access"
        assert payload["tier"] == "premium"

    def test_rejects_mismatched_purpose(self):
        token = create_token("user_xyz", "refresh")
        with pytest.raises(AuthenticationError, match="expected access"):
            decode_token_payload(token, "access")
