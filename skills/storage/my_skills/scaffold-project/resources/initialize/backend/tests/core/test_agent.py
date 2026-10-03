from __future__ import annotations

import pytest
from pydantic_ai.models.test import TestModel

from src.core.agents import GeneralAgent, Agent, ToolCallRecord
from src.core.validators import GeneralAgentValidator
from src.schema import AgentOutput
from src.helpers import ValidationError


class TestGeneralAgentValidator:
    def test_valid_output_passes(self):
        validator = GeneralAgentValidator()
        output = AgentOutput(
            summary="Completed analysis",
            content="Detailed results here",
            tools_used=["tool_a"],
            tool_calls=[ToolCallRecord(tool_name="tool_a", tool_args={}, output="ok")],
            status="completed",
        )
        valid, errors = validator.validate(output)
        assert valid is True
        assert len(errors) == 0
        validator.validate_or_raise(output)

    def test_empty_summary_raises(self):
        with pytest.raises(Exception):
            AgentOutput(
                summary="",
                content="Content exists",
                status="completed",
            )

    def test_whitespace_summary_raises(self):
        validator = GeneralAgentValidator()
        output = AgentOutput(
            summary="   ",
            content="Content exists",
            status="completed",
        )
        valid, errors = validator.validate(output)
        assert valid is False
        with pytest.raises(ValidationError):
            validator.validate_or_raise(output)

    def test_empty_content_raises(self):
        with pytest.raises(Exception):
            AgentOutput(
                summary="Summary exists",
                content="",
                status="completed",
            )

    def test_invalid_status_raises(self):
        with pytest.raises(Exception):
            AgentOutput(
                summary="Summary",
                content="Content",
                status="unknown_status",
            )


class TestGeneralAgent:
    def test_init_success(self):
        agent = GeneralAgent()
        assert agent.agent_name == "agent.general"
        assert agent.client_index == 0
        assert agent.system_prompt != ""

    def test_empty_system_prompt_raises(self):
        with pytest.raises(ValidationError):
            Agent(
                output_type=AgentOutput,
                system_prompt="   ",
                validator=GeneralAgentValidator(),
                agent_name="test_agent",
            )

    def test_empty_agent_name_raises(self):
        with pytest.raises(ValidationError):
            Agent(
                output_type=AgentOutput,
                system_prompt="Valid prompt",
                validator=GeneralAgentValidator(),
                agent_name="",
            )

    def test_client_index_out_of_range_raises(self):
        agent = GeneralAgent(client_index=999)
        with pytest.raises(ValidationError):
            agent._build_agent()

    @pytest.mark.asyncio
    async def test_empty_raw_information_raises(self):
        agent = GeneralAgent()
        with pytest.raises(ValidationError):
            await agent.run_async("")

    @pytest.mark.asyncio
    async def test_run_async_with_mock_model(self):
        mock_output = {
            "summary": "Processed query",
            "content": "Full response content here",
            "tools_used": [],
            "status": "completed",
        }
        model = TestModel(custom_output_args=mock_output)
        agent = GeneralAgent(model=model)

        result = await agent.run_async("What is the system status?")
        assert result.summary == "Processed query"
        assert result.content == "Full response content here"
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_run_async_with_additional_instructions(self):
        mock_output = {
            "summary": "Processed with instructions",
            "content": "Specific format output",
            "tools_used": [],
            "status": "completed",
        }
        model = TestModel(custom_output_args=mock_output)
        agent = GeneralAgent(model=model)

        result = await agent.run_async("Analyze logs", additional_instructions="Format as bullet points")
        assert result.summary == "Processed with instructions"

    def test_run_sync_bridge(self):
        mock_output = {
            "summary": "Sync execution",
            "content": "Executed via sync bridge",
            "tools_used": [],
            "status": "completed",
        }
        model = TestModel(custom_output_args=mock_output)
        agent = GeneralAgent(model=model)

        result = agent.run("Perform sync computation")
        assert result.summary == "Sync execution"
        assert result.content == "Executed via sync bridge"
