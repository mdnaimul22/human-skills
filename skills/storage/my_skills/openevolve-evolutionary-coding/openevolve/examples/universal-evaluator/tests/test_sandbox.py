import asyncio
from pathlib import Path
import pytest

from evaluator.bridge import OpenEvolveBridge
from evaluator.collectors.runtime import RuntimeCollector
from evaluator.collectors.test import TestCollector
from evaluator.engine import EvaluationEngine
from evaluator.models.candidate import Candidate
from evaluator.models.spec import EvaluationSpec
from evaluator.sandbox.base import Sandbox
from evaluator.sandbox.docker import DockerSandbox
from evaluator.sandbox.host import HostSandbox


class MockTrackingSandbox(Sandbox):
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.invocations: list[list[str]] = []

    async def run(
        self,
        command: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        self.invocations.append(command)
        return self.returncode, self.stdout, self.stderr


@pytest.mark.asyncio
async def test_host_sandbox_run_success(tmp_path: Path):
    sandbox = HostSandbox()
    code, out, err = await sandbox.run(["python", "-c", "print('hello_sandbox')"], cwd=tmp_path, timeout_seconds=5.0)
    assert code == 0
    assert "hello_sandbox" in out


@pytest.mark.asyncio
async def test_host_sandbox_timeout(tmp_path: Path):
    sandbox = HostSandbox()
    code, out, err = await sandbox.run(["python", "-c", "import time; time.sleep(2)"], cwd=tmp_path, timeout_seconds=0.1)
    assert code == 124
    assert "timed out" in err


@pytest.mark.asyncio
async def test_host_sandbox_custom_env(tmp_path: Path):
    sandbox = HostSandbox()
    code, out, err = await sandbox.run(
        ["python", "-c", "import os; print(os.getenv('CUSTOM_VAR'))"],
        cwd=tmp_path,
        timeout_seconds=5.0,
        env={"CUSTOM_VAR": "UE_SANDBOX_ACTIVE"},
    )
    assert code == 0
    assert "UE_SANDBOX_ACTIVE" in out


def test_docker_sandbox_security_vector_hardening(tmp_path: Path):
    sandbox = DockerSandbox(
        image="python:3.12-slim",
        memory_limit="256m",
        cpus="0.5",
        pids_limit=50,
        user="2000:2000",
        writable_workspace=False,
    )
    cmd = sandbox.build_docker_command(["python", "main.py"], cwd=tmp_path, env={"KEY": "VAL"})

    assert "--init" in cmd
    assert "--network" in cmd and cmd[cmd.index("--network") + 1] == "none"
    assert "--read-only" in cmd
    assert "--cap-drop" in cmd and cmd[cmd.index("--cap-drop") + 1] == "ALL"
    assert "--security-opt" in cmd and cmd[cmd.index("--security-opt") + 1] == "no-new-privileges:true"
    assert "--user" in cmd and cmd[cmd.index("--user") + 1] == "2000:2000"
    assert "--pids-limit" in cmd and cmd[cmd.index("--pids-limit") + 1] == "50"
    assert "--cpus" in cmd and cmd[cmd.index("--cpus") + 1] == "0.5"
    assert "--memory" in cmd and cmd[cmd.index("--memory") + 1] == "256m"
    assert "--memory-swap" in cmd and cmd[cmd.index("--memory-swap") + 1] == "256m"
    assert "--tmpfs" in cmd and cmd[cmd.index("--tmpfs") + 1] == "/tmp:rw,noexec,nosuid,size=64m"
    assert "-e" in cmd and "PYTHONDONTWRITEBYTECODE=1" in cmd
    assert "-e" in cmd and "TMPDIR=/tmp" in cmd
    assert "-e" in cmd and "KEY=VAL" in cmd
    assert f"{tmp_path.resolve()}:/workspace:ro" in cmd
    assert "python:3.12-slim" in cmd


def test_docker_sandbox_writable_workspace_flag(tmp_path: Path):
    sandbox = DockerSandbox(writable_workspace=True)
    cmd = sandbox.build_docker_command(["python", "main.py"], cwd=tmp_path)
    assert f"{tmp_path.resolve()}:/workspace:rw" in cmd


@pytest.mark.asyncio
async def test_test_collector_invokes_injected_sandbox(tmp_path: Path):
    candidate = Candidate(candidate_id="c1", root=tmp_path, entrypoint="main.py", language="python")
    spec = EvaluationSpec.model_validate({
        "evaluation_id": "test-spec",
        "objective": "test",
        "tests": [{"name": "unit", "command": ["pytest", "-q"]}],
        "fitness": {"metrics": [{"id": "test_pass_rate", "direction": "maximize", "weight": 1.0}]},
    })
    mock_sandbox = MockTrackingSandbox(returncode=0, stdout="1 passed")
    setattr(spec, "_sandbox", mock_sandbox)

    collector = TestCollector()
    evidence = await collector.collect(candidate, spec)

    assert len(mock_sandbox.invocations) == 1
    assert mock_sandbox.invocations[0] == ["pytest", "-q"]
    assert evidence[0].value == 1.0


@pytest.mark.asyncio
async def test_runtime_collector_invokes_injected_sandbox(tmp_path: Path):
    main_file = tmp_path / "main.py"
    main_file.write_text("print('done')\n")
    candidate = Candidate(candidate_id="c1", root=tmp_path, entrypoint="main.py", language="python")
    spec = EvaluationSpec.model_validate({
        "evaluation_id": "test-runtime",
        "objective": "runtime",
        "fitness": {"metrics": [{"id": "runtime_ms", "direction": "minimize", "weight": 1.0}]},
    })
    mock_sandbox = MockTrackingSandbox(returncode=0)
    setattr(spec, "_sandbox", mock_sandbox)

    collector = RuntimeCollector()
    evidence = await collector.collect(candidate, spec)

    assert len(mock_sandbox.invocations) == 1
    assert mock_sandbox.invocations[0] == ["python", str(main_file)]
    assert evidence[0].status.value == "passed"


@pytest.mark.asyncio
async def test_engine_propagates_sandbox_to_execution(tmp_path: Path):
    main_file = tmp_path / "main.py"
    main_file.write_text("print('ok')\n")
    candidate = Candidate(candidate_id="c1", root=tmp_path, entrypoint="main.py", language="python")
    spec = EvaluationSpec.model_validate({
        "evaluation_id": "test-engine-sandbox",
        "objective": "engine",
        "collectors": [{"id": "runtime", "type": "runtime"}],
        "fitness": {"metrics": [{"id": "runtime_ms", "direction": "minimize", "weight": 1.0, "normalization": {"minimum": 0, "maximum": 1000}}]},
    })
    mock_sandbox = MockTrackingSandbox(returncode=0)
    engine = EvaluationEngine(sandbox=mock_sandbox)
    run = await engine.evaluate(candidate, spec)

    assert len(mock_sandbox.invocations) == 1
    assert run.fitness.valid is True


def test_bridge_wires_sandbox(tmp_path: Path):
    candidate_file = tmp_path / "valid.py"
    candidate_file.write_text("def solve(): return 1\n")
    spec = EvaluationSpec.model_validate({
        "evaluation_id": "bridge-sandbox-spec",
        "objective": "bridge",
        "collectors": [{"id": "runtime", "type": "runtime"}],
        "fitness": {"metrics": [{"id": "runtime_ms", "direction": "minimize", "weight": 1.0, "normalization": {"minimum": 0, "maximum": 1000}}]},
    })
    mock_sandbox = MockTrackingSandbox(returncode=0)
    bridge = OpenEvolveBridge(spec, sandbox=mock_sandbox)
    res = bridge.evaluate(candidate_file)

    assert res.metrics["valid"] == 1.0
    assert len(mock_sandbox.invocations) >= 1
