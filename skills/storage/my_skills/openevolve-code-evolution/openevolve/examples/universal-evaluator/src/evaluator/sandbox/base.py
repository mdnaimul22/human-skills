from abc import ABC, abstractmethod
from pathlib import Path


class Sandbox(ABC):
    @abstractmethod
    async def run(
        self,
        command: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        raise NotImplementedError
