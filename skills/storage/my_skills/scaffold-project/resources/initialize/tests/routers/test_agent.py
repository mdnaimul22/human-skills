from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from src.core.auth import create_token
from src.db import UserRepository
from src.schema import AgentResponse, AgentOutput


class TestAgentRouter:
    @pytest.mark.asyncio
    async def test_run_agent_unauthorized_without_token(self, client: AsyncClient):
        resp = await client.post("/api/agent/run", json={"prompt": "Hello agent"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_run_agent_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/api/agent/run",
            json={"prompt": "Hello agent"},
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_run_agent_empty_prompt_returns_422(self, client: AsyncClient, db_session):
        repo = UserRepository(db_session)
        user = await repo.create(
            email="agent_test@example.com",
            name="Agent Test User",
            password_hash="mock_hash",
        )
        await db_session.commit()
        token = create_token(user.id, "access")

        resp = await client.post(
            "/api/agent/run",
            json={"prompt": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_run_agent_success_with_auth(self, client: AsyncClient, db_session):
        repo = UserRepository(db_session)
        user = await repo.create(
            email="agent_exec@example.com",
            name="Agent Exec User",
            password_hash="mock_hash",
        )
        await db_session.commit()
        token = create_token(user.id, "access")

        mock_response = AgentResponse(
            output=AgentOutput(
                summary="Agent task finished",
                content="Comprehensive answer content",
                tools_used=[],
                status="completed",
            ),
            duration_ms=45.2,
            client_index=0,
        )

        with patch("src.services.agent.AgentService.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_response

            resp = await client.post(
                "/api/agent/run",
                json={"prompt": "Generate summary"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["output"]["summary"] == "Agent task finished"
        assert data["output"]["content"] == "Comprehensive answer content"
        assert data["duration_ms"] == 45.2
