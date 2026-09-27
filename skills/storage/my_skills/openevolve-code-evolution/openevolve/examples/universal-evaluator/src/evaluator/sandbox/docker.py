import asyncio
from pathlib import Path

from .base import Sandbox


class DockerSandbox(Sandbox):
    def __init__(
        self,
        image: str = "python:3.12-slim",
        memory_limit: str = "512m",
        cpus: str = "1.0",
        pids_limit: int = 100,
        user: str = "1000:1000",
        writable_workspace: bool = False,
    ):
        self.image = image
        self.memory_limit = memory_limit
        self.cpus = cpus
        self.pids_limit = pids_limit
        self.user = user
        self.writable_workspace = writable_workspace

    def build_docker_command(
        self,
        command: list[str],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> list[str]:
        mount_mode = "rw" if self.writable_workspace else "ro"
        cmd = [
            "docker", "run", "--rm",
            "--init",
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--user", self.user,
            "--pids-limit", str(self.pids_limit),
            "--cpus", self.cpus,
            "--memory", self.memory_limit,
            "--memory-swap", self.memory_limit,
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "TMPDIR=/tmp",
            "-v", f"{cwd.resolve()}:/workspace:{mount_mode}",
            "-w", "/workspace",
        ]
        for key, val in (env or {}).items():
            cmd.extend(["-e", f"{key}={val}"])
        cmd.append(self.image)
        cmd.extend(command)
        return cmd

    async def run(
        self,
        command: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        docker_cmd = self.build_docker_command(command, cwd, env)
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return 124, "", "sandbox timeout"
        return proc.returncode or 0, out.decode(errors="replace"), err.decode(errors="replace")
