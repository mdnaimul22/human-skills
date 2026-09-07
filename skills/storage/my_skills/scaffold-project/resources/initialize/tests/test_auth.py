"""
Tests for authentication flows (registration, login, profile, 401 unauthenticated).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_lifecycle(client: AsyncClient):
    # 1. Register a new user
    register_payload = {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "SecurePassword123!",
    }
    reg_resp = await client.post("/api/auth/register", json=register_payload)
    assert reg_resp.status_code == 200, reg_resp.text
    reg_data = reg_resp.json()
    assert "token" in reg_data
    assert reg_data["email"] == "testuser@example.com"
    token = reg_data["token"]

    # 2. Duplicate registration should raise 409 Conflict
    dup_resp = await client.post("/api/auth/register", json=register_payload)
    assert dup_resp.status_code == 409

    # 3. Successful Login
    login_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
    }
    login_resp = await client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "token" in login_data

    # 4. Failed Login with invalid password (401 Unauthorized)
    bad_login_resp = await client.post(
        "/api/auth/login",
        json={"email": "testuser@example.com", "password": "WrongPassword!"},
    )
    assert bad_login_resp.status_code == 401

    # 5. Access /me without Authorization header (401 Unauthorized)
    unauth_resp = await client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # 6. Access /me with valid Bearer token (200 OK)
    me_resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "testuser@example.com"
    assert me_data["name"] == "Test User"
    assert "id" in me_data
