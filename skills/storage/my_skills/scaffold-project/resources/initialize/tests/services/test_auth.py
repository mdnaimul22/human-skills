from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from src.core.auth import create_token
from src.db import UserRepository
from src.helpers import (
    ConflictError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ValidationError,
)
from src.services import auth as auth_service


class TestRegister:
    @pytest.mark.asyncio
    async def test_creates_user_returns_register_response(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock) as mock_email:
            mock_email.return_value = True
            result = await auth_service.register(
                "new@example.com", "New User", "password123", db_session,
            )

        assert result.email == "new@example.com"
        assert "verify" in result.message.lower() or "check" in result.message.lower()
        assert not hasattr(result, "access_token")

    @pytest.mark.asyncio
    async def test_sends_verification_email(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock) as mock_email:
            mock_email.return_value = True
            await auth_service.register("verify@example.com", "V User", "pass123456", db_session)

        mock_email.assert_called_once()
        call_args = mock_email.call_args
        assert call_args[0][0] == "verify@example.com"
        assert call_args[0][1] == "V User"
        assert len(call_args[0][2]) > 50

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_conflict(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("dup@example.com", "First", "pass123456", db_session)

            with pytest.raises(ConflictError, match="already registered"):
                await auth_service.register("dup@example.com", "Second", "pass654321", db_session)

    @pytest.mark.asyncio
    async def test_user_created_with_email_unverified(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("unv@example.com", "Unv", "pass123456", db_session)

        repo = UserRepository(db_session)
        user = await repo.find_by_email("unv@example.com")
        assert user is not None
        assert user.email_verified is False
        assert user.auth_method == "local"

    @pytest.mark.asyncio
    async def test_email_send_failure_does_not_block_registration(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock) as mock_email:
            mock_email.side_effect = Exception("SMTP down")
            result = await auth_service.register("fail@example.com", "Fail", "pass123456", db_session)

        assert result.email == "fail@example.com"
        repo = UserRepository(db_session)
        user = await repo.find_by_email("fail@example.com")
        assert user is not None


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_verifies_and_returns_tokens(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("ver@example.com", "Ver", "pass123456", db_session)

        repo = UserRepository(db_session)
        user = await repo.find_by_email("ver@example.com")
        token = create_token(user.id, "verify_email")

        result = await auth_service.verify_email(token, db_session)
        assert result.access_token
        assert result.refresh_token
        assert result.email == "ver@example.com"

    @pytest.mark.asyncio
    async def test_already_verified_raises_validation_error(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("alr@example.com", "Alr", "pass123456", db_session)

        repo = UserRepository(db_session)
        user = await repo.find_by_email("alr@example.com")
        token = create_token(user.id, "verify_email")

        await auth_service.verify_email(token, db_session)

        with pytest.raises(ValidationError, match="already verified"):
            token2 = create_token(user.id, "verify_email")
            await auth_service.verify_email(token2, db_session)

    @pytest.mark.asyncio
    async def test_invalid_token_raises_auth_error(self, db_session):
        with pytest.raises(AuthenticationError):
            await auth_service.verify_email("invalid.token.here", db_session)

    @pytest.mark.asyncio
    async def test_access_token_cannot_verify_email(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("cross@example.com", "Cross", "pass123456", db_session)

        repo = UserRepository(db_session)
        user = await repo.find_by_email("cross@example.com")
        access_token = create_token(user.id, "access")

        with pytest.raises(AuthenticationError, match="expected verify_email"):
            await auth_service.verify_email(access_token, db_session)


class TestLogin:
    @pytest.mark.asyncio
    async def _register_and_verify(self, db_session, email="login@example.com", password="pass123456"):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register(email, "Login User", password, db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email(email)
        token = create_token(user.id, "verify_email")
        await auth_service.verify_email(token, db_session)
        return user

    @pytest.mark.asyncio
    async def test_successful_login_returns_tokens(self, db_session):
        await self._register_and_verify(db_session)
        result = await auth_service.login("login@example.com", "pass123456", db_session)
        assert result.access_token
        assert result.refresh_token
        assert result.email == "login@example.com"

    @pytest.mark.asyncio
    async def test_wrong_password_raises_auth_error(self, db_session):
        await self._register_and_verify(db_session)
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await auth_service.login("login@example.com", "wrongPassword", db_session)

    @pytest.mark.asyncio
    async def test_nonexistent_email_raises_auth_error(self, db_session):
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await auth_service.login("ghost@example.com", "anyPass", db_session)

    @pytest.mark.asyncio
    async def test_unverified_email_raises_auth_error(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("notveri@example.com", "Nv", "pass123456", db_session)

        with pytest.raises(AuthenticationError, match="not verified"):
            await auth_service.login("notveri@example.com", "pass123456", db_session)

    @pytest.mark.asyncio
    async def test_inactive_user_raises_permission_denied(self, db_session):
        await self._register_and_verify(db_session, email="inactive@example.com")
        repo = UserRepository(db_session)
        await repo.update("inactive@example.com".replace("@example.com", ""), is_active=False)
        user = await repo.find_by_email("inactive@example.com")
        await repo.update(user.id, is_active=False)
        await db_session.commit()

        with pytest.raises(PermissionDeniedError, match="inactive"):
            await auth_service.login("inactive@example.com", "pass123456", db_session)


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_valid_refresh_returns_new_tokens(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("ref@example.com", "Ref", "pass123456", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("ref@example.com")
        token = create_token(user.id, "verify_email")
        await auth_service.verify_email(token, db_session)

        login_result = await auth_service.login("ref@example.com", "pass123456", db_session)
        result = await auth_service.refresh_tokens(login_result.refresh_token, db_session)
        assert result.access_token
        assert result.refresh_token
        assert result.access_token
        assert result.refresh_token

    @pytest.mark.asyncio
    async def test_access_token_cannot_refresh(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("acr@example.com", "Acr", "pass123456", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("acr@example.com")
        token = create_token(user.id, "verify_email")
        await auth_service.verify_email(token, db_session)

        login_result = await auth_service.login("acr@example.com", "pass123456", db_session)
        with pytest.raises(AuthenticationError, match="expected refresh"):
            await auth_service.refresh_tokens(login_result.access_token, db_session)


class TestPasswordReset:
    @pytest.mark.asyncio
    async def test_request_reset_sends_email(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("rst@example.com", "Rst", "pass123456", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("rst@example.com")
        await repo.set_email_verified(user.id)
        await db_session.commit()

        with patch("src.services.auth.send_password_reset_email", new_callable=AsyncMock) as mock_reset:
            mock_reset.return_value = True
            await auth_service.request_password_reset("rst@example.com", db_session)

        mock_reset.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_reset_nonexistent_email_is_silent(self, db_session):
        with patch("src.services.auth.send_password_reset_email", new_callable=AsyncMock) as mock_reset:
            await auth_service.request_password_reset("noone@example.com", db_session)

        mock_reset.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_password_changes_password(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("rp@example.com", "Rp", "oldPass123", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("rp@example.com")
        await repo.set_email_verified(user.id)
        await db_session.commit()

        reset_token = create_token(user.id, "reset_password")
        await auth_service.reset_password(reset_token, "newPass456", db_session)

        result = await auth_service.login("rp@example.com", "newPass456", db_session)
        assert result.access_token

    @pytest.mark.asyncio
    async def test_reset_with_access_token_fails(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("badt@example.com", "Badt", "pass123456", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("badt@example.com")

        access_token = create_token(user.id, "access")
        with pytest.raises(AuthenticationError, match="expected reset_password"):
            await auth_service.reset_password(access_token, "newPass456", db_session)


class TestChangePassword:
    @pytest.mark.asyncio
    async def test_changes_password_successfully(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("cp@example.com", "Cp", "oldPass123", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("cp@example.com")
        await repo.set_email_verified(user.id)
        await db_session.commit()

        await auth_service.change_password(user.id, "oldPass123", "newPass456", db_session)

        result = await auth_service.login("cp@example.com", "newPass456", db_session)
        assert result.access_token

    @pytest.mark.asyncio
    async def test_wrong_current_password_raises_auth_error(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("cw@example.com", "Cw", "correctPass", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("cw@example.com")

        with pytest.raises(AuthenticationError, match="Current password is incorrect"):
            await auth_service.change_password(user.id, "wrongPass", "newPass456", db_session)


class TestUpdateProfile:
    @pytest.mark.asyncio
    async def test_updates_name(self, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await auth_service.register("up@example.com", "Old Name", "pass123456", db_session)
        repo = UserRepository(db_session)
        user = await repo.find_by_email("up@example.com")

        result = await auth_service.update_profile(user.id, "New Name", db_session)
        assert result.name == "New Name"
        assert result.email == "up@example.com"

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            await auth_service.update_profile("nonexistent_id_12345678", "Name", db_session)
