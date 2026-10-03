from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.core.auth import create_token
from src.db import UserRepository


class TestRegisterEndpoint:
    @pytest.mark.asyncio
    async def test_register_returns_message_not_tokens(self, client: AsyncClient):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            resp = await client.post("/api/auth/register", json={
                "email": "reg@example.com",
                "name": "Reg User",
                "password": "securePass123",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert data["email"] == "reg@example.com"
        assert "access_token" not in data
        assert "refresh_token" not in data

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self, client: AsyncClient):
        payload = {"email": "dup@example.com", "name": "Dup", "password": "pass123456"}
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json=payload)
            resp = await client.post("/api/auth/register", json=payload)

        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_email_returns_400(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "name": "Bad",
            "password": "pass123456",
        })
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_short_password_returns_422(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "short@example.com",
            "name": "Short",
            "password": "12345",
        })
        assert resp.status_code == 422


class TestVerifyEmailEndpoint:
    @pytest.mark.asyncio
    async def test_valid_token_returns_auth_tokens(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "vere@example.com",
                "name": "VerE",
                "password": "pass123456",
            })

        repo = UserRepository(db_session)
        user = await repo.find_by_email("vere@example.com")
        token = create_token(user.id, "verify_email")

        resp = await client.get(f"/api/auth/verify-email?token={token}")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/auth/verify-email?token=invalid.jwt.token")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token_returns_422(self, client: AsyncClient):
        resp = await client.get("/api/auth/verify-email")
        assert resp.status_code == 422


class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def _register_and_verify(self, client, db_session, email="log@example.com"):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": email, "name": "LogUser", "password": "pass123456",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email(email)
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")
        return user

    @pytest.mark.asyncio
    async def test_valid_login_returns_tokens(self, client: AsyncClient, db_session):
        await self._register_and_verify(client, db_session)
        resp = await client.post("/api/auth/login", json={
            "email": "log@example.com",
            "password": "pass123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, client: AsyncClient, db_session):
        await self._register_and_verify(client, db_session, email="wp@example.com")
        resp = await client.post("/api/auth/login", json={
            "email": "wp@example.com",
            "password": "wrongPassword",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_unverified_email_returns_401(self, client: AsyncClient):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "unv@example.com", "name": "Unv", "password": "pass123456",
            })

        resp = await client.post("/api/auth/login", json={
            "email": "unv@example.com",
            "password": "pass123456",
        })
        assert resp.status_code == 401


class TestRefreshEndpoint:
    @pytest.mark.asyncio
    async def test_valid_refresh_returns_new_tokens(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "rfr@example.com", "name": "Rfr", "password": "pass123456",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("rfr@example.com")
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")

        login_resp = await client.post("/api/auth/login", json={
            "email": "rfr@example.com", "password": "pass123456",
        })
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_access_token_as_refresh_returns_401(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "brf@example.com", "name": "Brf", "password": "pass123456",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("brf@example.com")
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")

        login_resp = await client.post("/api/auth/login", json={
            "email": "brf@example.com", "password": "pass123456",
        })
        access_token = login_resp.json()["access_token"]

        resp = await client.post("/api/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401


class TestMeEndpoint:
    @pytest.mark.asyncio
    async def test_authenticated_returns_profile(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "me@example.com", "name": "Me User", "password": "pass123456",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("me@example.com")
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")

        login_resp = await client.post("/api/auth/login", json={
            "email": "me@example.com", "password": "pass123456",
        })
        access_token = login_resp.json()["access_token"]

        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@example.com"
        assert data["email_verified"] is True
        assert data["auth_method"] == "local"

    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_returns_401(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "rft@example.com", "name": "Rft", "password": "pass123456",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("rft@example.com")
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")

        login_resp = await client.post("/api/auth/login", json={
            "email": "rft@example.com", "password": "pass123456",
        })
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_bearer_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token"})
        assert resp.status_code == 401


class TestUpdateProfileEndpoint:
    @pytest.mark.asyncio
    async def test_patch_name_succeeds(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "upd@example.com", "name": "Old Name", "password": "pass123456",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("upd@example.com")
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")

        login_resp = await client.post("/api/auth/login", json={
            "email": "upd@example.com", "password": "pass123456",
        })
        access_token = login_resp.json()["access_token"]

        resp = await client.patch(
            "/api/auth/me",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"


class TestChangePasswordEndpoint:
    @pytest.mark.asyncio
    async def test_change_password_succeeds(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "chp@example.com", "name": "Chp", "password": "oldPass123",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("chp@example.com")
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")

        login_resp = await client.post("/api/auth/login", json={
            "email": "chp@example.com", "password": "oldPass123",
        })
        access_token = login_resp.json()["access_token"]

        resp = await client.post(
            "/api/auth/change-password",
            json={"current_password": "oldPass123", "new_password": "newPass456"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200

        login2 = await client.post("/api/auth/login", json={
            "email": "chp@example.com", "password": "newPass456",
        })
        assert login2.status_code == 200


class TestForgotResetPasswordEndpoint:
    @pytest.mark.asyncio
    async def test_forgot_password_always_returns_200(self, client: AsyncClient):
        with patch("src.services.auth.send_password_reset_email", new_callable=AsyncMock):
            resp = await client.post("/api/auth/forgot-password", json={
                "email": "nonexistent@example.com",
            })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_password_with_valid_token(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "rsp@example.com", "name": "Rsp", "password": "oldPass123",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("rsp@example.com")
        await repo.set_email_verified(user.id)
        await db_session.commit()

        reset_token = create_token(user.id, "reset_password")
        resp = await client.post("/api/auth/reset-password", json={
            "token": reset_token, "new_password": "resetPass789",
        })
        assert resp.status_code == 200

        login_resp = await client.post("/api/auth/login", json={
            "email": "rsp@example.com", "password": "resetPass789",
        })
        assert login_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_with_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.post("/api/auth/reset-password", json={
            "token": "invalid.jwt.token", "new_password": "newPass123",
        })
        assert resp.status_code == 401


class TestLogoutEndpoint:
    @pytest.mark.asyncio
    async def test_logout_returns_ok(self, client: AsyncClient, db_session):
        with patch("src.services.auth.send_verification_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "out@example.com", "name": "Out", "password": "pass123456",
            })
        repo = UserRepository(db_session)
        user = await repo.find_by_email("out@example.com")
        token = create_token(user.id, "verify_email")
        await client.get(f"/api/auth/verify-email?token={token}")

        login_resp = await client.post("/api/auth/login", json={
            "email": "out@example.com", "password": "pass123456",
        })
        access_token = login_resp.json()["access_token"]

        resp = await client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        assert "logout" in resp.json()["message"].lower() or "clear" in resp.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_logout_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.post("/api/auth/logout")
        assert resp.status_code == 401
