from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ToolStatus(str, Enum):
    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    NOT_FOUND = "not_found"
    CRASHED = "crashed"


@dataclass
class Response:
    message: str
    break_loop: bool = False
    additional: Optional[dict[str, Any]] = None
    success: bool = True
    status: Optional[ToolStatus] = None
    duration_ms: float = 0.0
    error_code: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status is None:
            self.status = ToolStatus.SUCCESS if self.success else ToolStatus.EXECUTION_ERROR
        else:
            self.success = (self.status == ToolStatus.SUCCESS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value if isinstance(self.status, ToolStatus) else str(self.status),
            "success": self.success,
            "message": self.message,
            "break_loop": self.break_loop,
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
            "additional": self.additional or {},
        }


class Tool:
    name: str = ""
    description: str = ""
    arguments: str = ""
    instruction: str = ""

    def __init__(self, args: Optional[dict[str, Any]] = None, name: str = "", **kwargs: Any) -> None:
        self.args: dict[str, Any] = args or {}
        self.name: str = name or self.__class__.__name__

    async def execute(self, **kwargs: Any) -> Response:
        raise NotImplementedError(f"{self.__class__.__name__}.execute() must be implemented.")
