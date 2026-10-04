from __future__ import annotations

import json
import time
from src.config import Settings, setup_logger
from src.schema import AgentRequest, AgentResponse, AgentOutput, AgentProfile
from src.core.agents import AgentFactory, Agent

logger = setup_logger(boss_name="services.main.txt", his_name="services.agent.txt")


class AgentService:
    def __init__(self, factory: AgentFactory | None = None) -> None:
        self.factory = factory or AgentFactory()
        self.agent: Agent[AgentOutput] | None = None

    def list_agents(self) -> list[AgentProfile]:
        return self.factory.list_profiles()

    def get_agent_profile(self, name: str) -> AgentProfile:
        return self.factory.get_profile(name)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.monotonic()
        agent = self.agent or self.factory.create(
            agent_name=request.agent_name,
            client_index=request.client_index,
        )
        logger.info(f"AgentService executing agent on client_index={agent.client_index}")

        raw_info = request.prompt
        if request.parameters:
            raw_info = f"{request.prompt}\n\nParameters:\n{json.dumps(request.parameters, indent=2)}"

        output: AgentOutput = await agent.run_async(
            raw_information=raw_info,
            additional_instructions=request.instructions,
        )
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        return AgentResponse(
            output=output,
            duration_ms=duration_ms,
            client_index=agent.client_index,
        )
