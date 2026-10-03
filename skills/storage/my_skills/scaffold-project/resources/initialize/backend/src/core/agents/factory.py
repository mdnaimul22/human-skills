from __future__ import annotations

from pydantic_ai.models import Model
from src.config import Settings, setup_logger, read_text, read_yaml, exists, list_files, get_rel_path
from src.schema import AgentProfile, AgentOutput
from src.core.validators import GeneralAgentValidator
from src.helpers import NotFoundError, ValidationError
from .base import Agent

logger = setup_logger(boss_name="core.agents.main.txt", his_name="core.agents.factory.txt")


class AgentRegistry:
    def __init__(self, auto_discover: bool = False) -> None:
        self._profiles: dict[str, AgentProfile] = {}
        if auto_discover:
            self.auto_discover()

    def register(self, profile: AgentProfile) -> None:
        name = profile.name.strip()
        if not name:
            raise ValidationError("Agent profile name cannot be empty")
        self._profiles[name] = profile
        logger.info(f"Registered agent profile: '{name}'")

    def register_from_yaml(self, yaml_path: str) -> AgentProfile:
        if not exists(yaml_path):
            raise NotFoundError(f"Agent config YAML not found: {yaml_path}")
        data = read_yaml(yaml_path)
        if not isinstance(data, dict):
            raise ValidationError(f"Invalid YAML content in {yaml_path}, expected dictionary")
        profile = AgentProfile.model_validate(data)
        self.register(profile)
        return profile

    def auto_discover(self, directories: tuple[str, ...] = ("data/agents",)) -> list[AgentProfile]:
        loaded: list[AgentProfile] = []
        for search_dir in directories:
            if exists(search_dir):
                for p in list_files(search_dir, "*.yaml"):
                    try:
                        rel = get_rel_path(p)
                        loaded.append(self.register_from_yaml(rel))
                    except Exception as exc:
                        logger.warning(f"Skipping invalid agent config in {p}: {exc}")
                for p in list_files(search_dir, "*.yml"):
                    try:
                        rel = get_rel_path(p)
                        loaded.append(self.register_from_yaml(rel))
                    except Exception as exc:
                        logger.warning(f"Skipping invalid agent config in {p}: {exc}")
        return loaded



    def get(self, name: str) -> AgentProfile:
        clean_name = name.strip()
        if clean_name not in self._profiles:
            raise NotFoundError(f"Agent profile '{clean_name}' not found")
        return self._profiles[clean_name]

    def list_profiles(self) -> list[AgentProfile]:
        return list(self._profiles.values())


class AgentFactory:
    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry
        self._rotation_counters: dict[str, int] = {}

    def _current_client_index(self, profile: AgentProfile, explicit_index: int | None) -> int:
        if explicit_index is not None:
            return explicit_index
        total_clients = len(Settings.LLM_CLIENTS)
        if total_clients == 0 or not profile.is_rotate:
            return profile.client_index
        current = self._rotation_counters.get(profile.name, 0)
        self._rotation_counters[profile.name] = (current + 1) % total_clients
        return current

    def _resolve_prompt(self, profile: AgentProfile) -> str:
        if profile.prompt_instruction:
            if exists(profile.prompt_instruction):
                return read_text(profile.prompt_instruction)
            return profile.prompt_instruction
        if profile.prompt_path:
            if exists(profile.prompt_path):
                return read_text(profile.prompt_path)
            raise NotFoundError(f"Prompt file not found for agent '{profile.name}': {profile.prompt_path}")
        raise NotFoundError(f"No prompt configured for agent '{profile.name}'")

    def create(
        self,
        agent_name: str = "general",
        client_index: int | None = None,
        model: Model | None = None,
    ) -> Agent[AgentOutput]:
        profile = self.registry.get(agent_name)
        prompt_content = self._resolve_prompt(profile)
        client_index = self._current_client_index(profile, client_index)

        return Agent[AgentOutput](
            output_type=AgentOutput,
            system_prompt=prompt_content,
            validator=GeneralAgentValidator(),
            agent_name=f"agent.{profile.name}",
            client_index=client_index,
            model=model,
        )


default_agent_registry = AgentRegistry()
default_agent_registry.auto_discover()
default_agent_factory = AgentFactory(default_agent_registry)

__all__ = [
    "AgentRegistry",
    "AgentFactory",
    "default_agent_registry",
    "default_agent_factory",
]
