from __future__ import annotations

import time
from src.config import Settings, setup_logger
from src.schema import AgentRequest, AgentResponse, AgentOutput
from src.core.agents import AgentFactory, default_agent_factory, Agent

logger = setup_logger(boss_name="services.main.txt", his_name="services.agent.txt")


class AgentService:
    def __init__(self, factory: AgentFactory = default_agent_factory) -> None:
        self.factory = factory
        self.agent: Agent[AgentOutput] | None = None

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.monotonic()
        agent = self.agent or self.factory.create(
            agent_name=request.agent_name,
            client_index=request.client_index,
        )
        logger.info(f"AgentService executing agent on client_index={agent.client_index}")
        output: AgentOutput = await agent.run_async(
            raw_information=request.prompt,
            additional_instructions=request.instructions,
        )
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        return AgentResponse(
            output=output,
            duration_ms=duration_ms,
            client_index=agent.client_index,
        )
