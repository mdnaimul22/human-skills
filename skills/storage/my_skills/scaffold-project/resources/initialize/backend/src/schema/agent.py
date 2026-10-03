from __future__ import annotations

from pydantic import BaseModel, Field, JsonValue, model_validator


class AgentProfile(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    description: str = Field(default="")
    prompt_path: str | None = Field(default=None)
    prompt_instruction: str | None = Field(default=None)
    client_index: int = Field(default=0, ge=0)
    is_rotate: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_prompt_source(self) -> AgentProfile:
        if not self.prompt_path and not self.prompt_instruction:
            raise ValueError("Either prompt_instruction or prompt_path must be provided")
        if not self.prompt_path and self.prompt_instruction:
            self.prompt_path = self.prompt_instruction
        return self



class ToolCallRecord(BaseModel):
    tool_name: str = Field(..., min_length=1)
    tool_args: dict[str, JsonValue] = Field(default_factory=dict)
    output: str = Field(default="")


class BaseAgentOutput(BaseModel):
    tools_used: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class AgentOutput(BaseAgentOutput):
    summary: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    status: str = Field(default="completed", pattern=r"^(completed|failed|requires_input)$")


class AgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    agent_name: str = Field(default="general", pattern=r"^[a-zA-Z0-9_-]+$")
    instructions: str | None = None
    client_index: int | None = Field(default=None, ge=0)


class AgentResponse(BaseModel):
    output: AgentOutput
    duration_ms: float = Field(default=0.0, ge=0)
    client_index: int = 0
