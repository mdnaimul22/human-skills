from __future__ import annotations

from src.schema import AgentOutput
from src.helpers import ValidationError


class GeneralAgentValidator:
    def validate(self, output: AgentOutput) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not output.summary or not output.summary.strip():
            errors.append("Summary cannot be empty")
        if not output.content or not output.content.strip():
            errors.append("Content cannot be empty")
        if output.status not in ("completed", "failed", "requires_input"):
            errors.append(f"Invalid status: {output.status}")
        return len(errors) == 0, errors

    def validate_or_raise(self, output: AgentOutput) -> None:
        valid, errors = self.validate(output)
        if not valid:
            raise ValidationError("; ".join(errors))
