from __future__ import annotations

import asyncio
import concurrent.futures
import subprocess
from typing import Generic, Protocol, TypeVar
from pydantic import BaseModel, Field, JsonValue
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.tools import Tool
from pydantic_ai.usage import UsageLimits

from src.config import Settings, setup_logger, get_abs_path
from src.schema import ToolCallRecord, BaseAgentOutput
from src.helpers import ValidationError

logger = setup_logger(boss_name="core.agents.main.txt", his_name="core.agents.base.txt")

T = TypeVar("T", bound=BaseAgentOutput)
ToolExecutionRecord = ToolCallRecord


class StageValidatorProtocol(Protocol[T]):
    def validate_or_raise(self, output: T) -> None:
        ...


class ToolInvocation(BaseModel):
    tool_name: str
    tool_args: dict[str, JsonValue] = Field(default_factory=dict)


def _strip_markdown(text: str) -> str:
    txt = text.strip()
    if txt.startswith("```"):
        lines = txt.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            return "\n".join(lines[1:-1]).strip()
        return txt.strip("`").strip()
    return txt


def _strip_cli_prefix(text: str) -> str:
    cli_prefix = text.strip()
    if cli_prefix.startswith("human-skills"):
        tail = cli_prefix[len("human-skills"):].strip()
        if (tail.startswith("'") and tail.endswith("'")) or (tail.startswith('"') and tail.endswith('"')):
            return tail[1:-1].strip()
        return tail
    return cli_prefix


def _parse_cli_flags(text: str) -> ToolInvocation | None:
    parts = text.strip().split()
    if len(parts) >= 3 and parts[0] == "human-skills" and parts[1] in ("--tool_info", "--skill_info"):
        return ToolInvocation(tool_name=parts[1].lstrip("-"), tool_args={"name": parts[2]})
    return None


def _parse_invocation(tool_name: str, tool_args: dict[str, JsonValue] | None = None) -> ToolInvocation:
    raw_text = _strip_markdown(tool_name)
    flag_inv = _parse_cli_flags(raw_text)
    if flag_inv is not None:
        return flag_inv

    payload_text = _strip_cli_prefix(raw_text)
    if payload_text.startswith("{"):
        try:
            return ToolInvocation.model_validate_json(payload_text)
        except Exception as e:
            logger.warning(f"Failed to parse JSON invocation payload: {e}")

    args = tool_args if tool_args is not None else {}
    return ToolInvocation(tool_name=raw_text, tool_args=args)


def _sandbox_args(args: dict[str, JsonValue]) -> dict[str, JsonValue]:
    guarded: dict[str, JsonValue] = {}
    path_keys = ("input_path", "directory_path", "search_directory", "absolute_path", "path", "file_path", "dir_path")
    for key, val in args.items():
        if key in path_keys:
            raw_path = str(val).strip()
            if raw_path == "/":
                raise ValidationError("Access denied: Scanning root directory '/' is forbidden")
            try:
                guarded[key] = get_abs_path(raw_path)
            except ValueError as e:
                raise ValidationError(str(e))
        else:
            guarded[key] = val
    return guarded


def _build_command(invocation: ToolInvocation) -> list[str]:
    tool_name = invocation.tool_name.strip()
    if not tool_name:
        raise ValidationError("tool_name cannot be empty, for more information execute human-skills --tool_info tool_name")

    guarded_args = _sandbox_args(invocation.tool_args)

    if tool_name in ("skill_info", "read_skill"):
        skill_name = str(guarded_args.get("name", "")).strip()
        if not skill_name:
            skill_name = str(guarded_args.get("skill_name", "")).strip()
        if not skill_name:
            raise ValidationError("skill_name is required for skill_info please provide exact 'skill_name')")
        return ["human-skills", "--skill_info", skill_name]

    if tool_name in ("tool_info", "inspect_tool"):
        target_tool = str(guarded_args.get("name", "")).strip()
        if not target_tool:
            target_tool = str(guarded_args.get("tool_name", "")).strip()
        if not target_tool:
            raise ValidationError("tool name is required for tool_info please provide exact 'tool_name')")
        return ["human-skills", "--tool_info", target_tool]

    if tool_name in ("list_skills", "discover"):
        category = str(guarded_args.get("category", "all")).strip()
        return ["human-skills", "--list", category]

    payload: str = ToolInvocation(tool_name=tool_name, tool_args=guarded_args).model_dump_json()
    return ["human-skills", payload]


def _execute_skill(tool_name: str, tool_args: dict[str, JsonValue] | None = None) -> str:
    try:
        invocation = _parse_invocation(tool_name, tool_args)
        cmd = _build_command(invocation)
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if process.returncode != 0 and not process.stdout:
            return f"Error executing {invocation.tool_name}: {process.stderr.strip()}"
        return process.stdout or process.stderr
    except ValidationError as e:
        return f"Tool Execution Error: {e}"
    except Exception as e:
        logger.error(f"Unexpected error executing tool '{tool_name}': {e}")
        return f"Tool Execution Error: {e}"


class Agent(Generic[T]):
    def __init__(
        self,
        output_type: type[T],
        system_prompt: str,
        validator: StageValidatorProtocol[T],
        agent_name: str,
        client_index: int = 0,
        model: Model | None = None,
    ):
        if not system_prompt.strip():
            raise ValidationError("system_prompt must not be empty")
        if not agent_name.strip():
            raise ValidationError("agent_name must not be empty")

        self.output_type: type[T] = output_type
        self.system_prompt: str = system_prompt
        self.validator: StageValidatorProtocol[T] = validator
        self.agent_name: str = agent_name
        self.client_index: int = client_index
        self.model: Model | None = model
        self.tool_call_history: list[ToolCallRecord] = []

    def _record_tool_call(self, tool_name: str, args: dict[str, JsonValue], output: str) -> None:
        self.tool_call_history.append(
            ToolCallRecord(
                tool_name=tool_name,
                tool_args=args,
                output=output.strip(),
            )
        )
        logger.info(f"Agent '{self.agent_name}' executed: {tool_name}")

    def _build_agent(self) -> PydanticAgent[None, T]:
        if self.model is not None:
            agent_model = self.model
        else:
            if not Settings.LLM_CLIENTS:
                raise ValidationError("No LLM clients configured in Settings.LLM_CLIENTS")
            if self.client_index >= len(Settings.LLM_CLIENTS):
                raise ValidationError(
                    f"Client index {self.client_index} out of range (total: {len(Settings.LLM_CLIENTS)})"
                )
            client = Settings.LLM_CLIENTS[self.client_index]
            provider = OpenAIProvider(base_url=client.base_url, api_key=client.api_key)
            agent_model = OpenAIChatModel(client.model, provider=provider)

        async def human_skills(tool_name: str, tool_args: dict[str, JsonValue] = {}) -> str:
            loop = asyncio.get_running_loop()
            output: str = await loop.run_in_executor(None, _execute_skill, tool_name, tool_args)
            self._record_tool_call(tool_name, tool_args, output)
            return output

        universal_tool = Tool(
            human_skills,
            description=(
                "Universal gateway to human-skills ecosystem. "
                "1. Run CLI tools: tool_name='tree_gen' / 'view_file' / 'linter' with tool_args. "
                "2. Read any skill instructions: tool_name='skill_info', tool_args={'name': '<skill_name>'}. "
                "3. Inspect tool schema: tool_name='tool_info', tool_args={'name': '<tool_name>'}."
            ),
        )

        return PydanticAgent(
            model=agent_model,
            output_type=self.output_type,
            system_prompt=self.system_prompt,
            retries=Settings.LLM_RETRIES,
            tools=[universal_tool],
        )

    @property
    def agent(self) -> PydanticAgent[None, T]:
        return self._build_agent()

    async def run_async(
        self,
        raw_information: str,
        additional_instructions: str | None = None,
    ) -> T:
        if not raw_information.strip():
            raise ValidationError("raw_information cannot be empty")

        self.tool_call_history.clear()
        prompt_lines: list[str] = [f"Context Information:\n{raw_information}"]
        if additional_instructions and additional_instructions.strip():
            prompt_lines.append(f"Additional Instructions:\n{additional_instructions.strip()}")

        user_prompt: str = "\n\n".join(prompt_lines)
        logger.info(f"Executing {self.agent_name} via universal human-skills bridge")

        result = await self.agent.run(
            user_prompt,
            usage_limits=UsageLimits(request_limit=5),
        )
        output: T = result.output

        if not output.tool_calls:
            output.tool_calls = list(self.tool_call_history)
        if not output.tools_used:
            output.tools_used = [r.tool_name for r in self.tool_call_history]

        self.validator.validate_or_raise(output)
        return output

    def run(
        self,
        raw_information: str,
        additional_instructions: str | None = None,
    ) -> T:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        coroutine = self.run_async(raw_information, additional_instructions)

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(asyncio.run, coroutine).result()

        return asyncio.run(coroutine)
