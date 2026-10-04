from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError
from src.schema import AgentProfile
from src.core.agents import AgentFactory
from src.helpers import NotFoundError, ValidationError
from src.config import write_yaml, delete


class TestAgentFactory:
    def test_default_factory_has_general(self):
        factory = AgentFactory()
        profile = factory.get_profile("general")
        assert profile.name == "general"
        assert profile.client_index == 0
        assert profile.prompt_instruction is not None
        assert "human-skills" in profile.prompt_instruction

    def test_register_and_get_profile(self):
        factory = AgentFactory(auto_discover=False)
        profile = AgentProfile(
            name="code_reviewer",
            description="Reviews code",
            prompt_instruction="Review python code for bugs.",
            client_index=1,
        )
        factory.register(profile)
        fetched = factory.get_profile("code_reviewer")
        assert fetched.name == "code_reviewer"
        assert fetched.client_index == 1
        assert fetched.prompt_instruction == "Review python code for bugs."

    def test_get_unknown_profile_raises(self):
        factory = AgentFactory(auto_discover=False)
        with pytest.raises(NotFoundError):
            factory.get_profile("non_existent_profile")

    def test_empty_profile_name_raises(self):
        factory = AgentFactory(auto_discover=False)
        with pytest.raises(ValidationError):
            profile = AgentProfile(
                name="valid_name",
                prompt_instruction="Instructions",
            )
            profile.name = "   "
            factory.register(profile)

    def test_factory_creates_agent_from_profile(self):
        factory = AgentFactory(auto_discover=True)
        agent = factory.create("general")
        assert agent.agent_name == "agent.general"
        assert agent.client_index == 0
        assert agent.system_prompt != ""

    def test_factory_with_client_index_override(self):
        factory = AgentFactory(auto_discover=True)
        agent = factory.create("general", client_index=2)
        assert agent.client_index == 2

    def test_factory_missing_prompt_file_raises(self):
        factory = AgentFactory(auto_discover=False)
        factory.register(
            AgentProfile(
                name="missing_prompt",
                prompt_path="data/does_not_exist.md",
            )
        )
        with pytest.raises(NotFoundError):
            factory.create("missing_prompt")

    def test_factory_round_robin_rotation(self):
        factory = AgentFactory(auto_discover=True)
        agent_1 = factory.create("general")
        agent_2 = factory.create("general")
        agent_3 = factory.create("general")
        assert agent_1.client_index == 0
        assert agent_2.client_index == 1
        assert agent_3.client_index == 0

    def test_factory_fixed_index_when_is_rotate_false(self):
        factory = AgentFactory(auto_discover=False)
        factory.register(
            AgentProfile(
                name="pinned_agent",
                prompt_instruction="Fixed system prompt",
                client_index=1,
                is_rotate=False,
            )
        )
        agent_1 = factory.create("pinned_agent")
        agent_2 = factory.create("pinned_agent")
        assert agent_1.client_index == 1
        assert agent_2.client_index == 1

    def test_factory_explicit_override_does_not_break_rotation(self):
        factory = AgentFactory(auto_discover=True)
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
            factory = AgentFactory(auto_discover=False)
            profile = factory.register_from_yaml(yaml_path)
            assert profile.name == "test_custom"
            assert profile.client_index == 1
            assert profile.is_rotate is False
            assert profile.prompt_instruction == "You are a custom YAML agent."

            agent = factory.create("test_custom")
            assert agent.agent_name == "agent.test_custom"
            assert agent.client_index == 1
            assert agent.system_prompt == "You are a custom YAML agent."
        finally:
            delete(yaml_path)

    def test_factory_with_inline_prompt_instruction(self):
        factory = AgentFactory(auto_discover=False)
        profile = AgentProfile(
            name="inline_agent",
            prompt_instruction="You are a specialized inline test assistant.",
            client_index=0,
            is_rotate=False,
        )
        factory.register(profile)
        agent = factory.create("inline_agent")
        assert agent.system_prompt == "You are a specialized inline test assistant."

    def test_factory_list_profiles(self):
        factory = AgentFactory(auto_discover=True)
        profiles = factory.list_profiles()
        assert len(profiles) >= 1
        assert any(p.name == "general" for p in profiles)

    def test_profile_requires_prompt_source(self):
        with pytest.raises(PydanticValidationError):
            AgentProfile(name="no_prompt_agent")
