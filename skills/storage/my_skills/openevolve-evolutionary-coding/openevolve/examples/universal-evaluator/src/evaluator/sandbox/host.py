import asyncio
import os
from pathlib import Path

from .base import Sandbox


class HostSandbox(Sandbox):
    async def run(
        self,
        command: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        environ = {**os.environ, **(env or {})}
        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=environ,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return 124, "", "process execution timed out"
        return proc.returncode or 0, out.decode(errors="replace"), err.decode(errors="replace")
