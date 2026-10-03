from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError
from src.schema import AgentProfile
from src.core.agents import AgentRegistry, AgentFactory, default_agent_registry
from src.helpers import NotFoundError, ValidationError
from src.config import write_yaml, delete


class TestAgentRegistryAndFactory:
    def test_default_registry_has_general(self):
        profile = default_agent_registry.get("general")
        assert profile.name == "general"
        assert profile.client_index == 0
        assert profile.prompt_instruction is not None
        assert "human-skills" in profile.prompt_instruction

    def test_register_and_get_profile(self):
        registry = AgentRegistry()
        profile = AgentProfile(
            name="code_reviewer",
            description="Reviews code",
            prompt_instruction="Review python code for bugs.",
            client_index=1,
        )
        registry.register(profile)
        fetched = registry.get("code_reviewer")
        assert fetched.name == "code_reviewer"
        assert fetched.client_index == 1
        assert fetched.prompt_instruction == "Review python code for bugs."

    def test_get_unknown_profile_raises(self):
        registry = AgentRegistry()
        with pytest.raises(NotFoundError):
            registry.get("non_existent_profile")

    def test_empty_profile_name_raises(self):
        registry = AgentRegistry()
        with pytest.raises(ValidationError):
            profile = AgentProfile(
                name="valid_name",
                prompt_instruction="Instructions",
            )
            profile.name = "   "
            registry.register(profile)

    def test_factory_requires_registry(self):
        with pytest.raises(TypeError):
            AgentFactory()

    def test_factory_creates_agent_from_profile(self):
        factory = AgentFactory(default_agent_registry)
        agent = factory.create("general")
        assert agent.agent_name == "agent.general"
        assert agent.client_index == 0
        assert agent.system_prompt != ""

    def test_factory_with_client_index_override(self):
        factory = AgentFactory(default_agent_registry)
        agent = factory.create("general", client_index=2)
        assert agent.client_index == 2

    def test_factory_missing_prompt_file_raises(self):
        registry = AgentRegistry()
        registry.register(
            AgentProfile(
                name="missing_prompt",
                prompt_path="data/does_not_exist.md",
            )
        )
        factory = AgentFactory(registry=registry)
        with pytest.raises(NotFoundError):
            factory.create("missing_prompt")

    def test_factory_round_robin_rotation(self):
        factory = AgentFactory(default_agent_registry)
        agent_1 = factory.create("general")
        agent_2 = factory.create("general")
        agent_3 = factory.create("general")
        assert agent_1.client_index == 0
        assert agent_2.client_index == 1
        assert agent_3.client_index == 0

    def test_factory_fixed_index_when_is_rotate_false(self):
        registry = AgentRegistry()
        registry.register(
            AgentProfile(
                name="pinned_agent",
                prompt_instruction="Fixed system prompt",
                client_index=1,
                is_rotate=False,
            )
        )
        factory = AgentFactory(registry)
        agent_1 = factory.create("pinned_agent")
        agent_2 = factory.create("pinned_agent")
        assert agent_1.client_index == 1
        assert agent_2.client_index == 1

    def test_factory_explicit_override_does_not_break_rotation(self):
        factory = AgentFactory(default_agent_registry)
        forced_agent = factory.create("general", client_index=5)
        assert forced_agent.client_index == 5

    def test_register_from_yaml_and_create(self):
        yaml_path = "data/agents/test_custom.yaml"
        payload = {
            "name": "test_custom",
            "description": "Custom agent loaded from YAML",
            "prompt_instruction": "You are a custom YAML agent.",
            "client_index": 1,
            "is_rotate": False,
        }
        write_yaml(yaml_path, payload)
        try:
            registry = AgentRegistry()
            profile = registry.register_from_yaml(yaml_path)
            assert profile.name == "test_custom"
            assert profile.client_index == 1
            assert profile.is_rotate is False
            assert profile.prompt_instruction == "You are a custom YAML agent."

            factory = AgentFactory(registry)
            agent = factory.create("test_custom")
            assert agent.agent_name == "agent.test_custom"
            assert agent.client_index == 1
            assert agent.system_prompt == "You are a custom YAML agent."
        finally:
            delete(yaml_path)

    def test_factory_with_inline_prompt_instruction(self):
        registry = AgentRegistry()
        profile = AgentProfile(
            name="inline_agent",
            prompt_instruction="You are a specialized inline test assistant.",
            client_index=0,
            is_rotate=False,
        )
        registry.register(profile)
        factory = AgentFactory(registry)
        agent = factory.create("inline_agent")
        assert agent.system_prompt == "You are a specialized inline test assistant."

    def test_profile_requires_prompt_source(self):
        with pytest.raises(PydanticValidationError):
            AgentProfile(name="no_prompt_agent")
