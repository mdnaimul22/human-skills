from __future__ import annotations

from pydantic_ai.models import Model
from src.schema import AgentOutput, ToolCallRecord
from src.core.validators import GeneralAgentValidator
from .base import Agent


class GeneralAgent(Agent[AgentOutput]):
    def __init__(
        self,
        client_index: int = 0,
        model: Model | None = None,
    ):
        from .factory import default_agent_registry
        profile = default_agent_registry.get("general")
        system_prompt = profile.prompt_instruction or ""
        super().__init__(
            output_type=AgentOutput,
            system_prompt=system_prompt,
            validator=GeneralAgentValidator(),
            agent_name="agent.general",
            client_index=client_index,
            model=model,
        )


__all__ = [
    "GeneralAgent",
    "ToolCallRecord",
]
