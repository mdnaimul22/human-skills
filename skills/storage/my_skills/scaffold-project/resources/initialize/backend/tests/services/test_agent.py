from __future__ import annotations

import pytest
from pydantic_ai.models.test import TestModel

from src.core.agents import GeneralAgent
from src.services.agent import AgentService
from src.schema import AgentRequest


class TestAgentService:
    @pytest.mark.asyncio
    async def test_service_execute_success(self):
        mock_output = {
            "summary": "Service executed",
            "content": "Result from service execution",
            "tools_used": [],
            "status": "completed",
        }
        service = AgentService()
        service.agent = GeneralAgent(model=TestModel(custom_output_args=mock_output))

        req = AgentRequest(prompt="Execute service task", client_index=0)
        res = await service.execute(req)

        assert res.output.summary == "Service executed"
        assert res.output.content == "Result from service execution"
        assert res.duration_ms >= 0.0
        assert res.client_index == 0

    @pytest.mark.asyncio
    async def test_service_duration_computed(self):
        mock_output = {
            "summary": "Fast execution",
            "content": "Duration measured",
            "tools_used": [],
            "status": "completed",
        }
        service = AgentService()
        service.agent = GeneralAgent(model=TestModel(custom_output_args=mock_output))

        res = await service.execute(AgentRequest(prompt="Check duration"))
        assert isinstance(res.duration_ms, float)

    @pytest.mark.asyncio
    async def test_service_empty_prompt_raises(self):
        with pytest.raises(Exception):
            AgentRequest(prompt="")
