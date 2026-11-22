from __future__ import annotations
import shlex
import shutil
import socket
import subprocess
import time
from typing import Callable, Optional
from src.config import Settings, setup_logger
from .schema import ContainerSpec, ContainerState, ContainerStatus
from .image import ImagePuller

logger = setup_logger(Settings.LOG_DIR / "docker.log", name="apps.docker.container")

def _sleep_interval(seconds: float) -> None:
    time.sleep(seconds)

def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

class ContainerEngine:
    @staticmethod
    def get_state(name: str, port: Optional[int] = None, host: str = "127.0.0.1") -> ContainerState:
        if not shutil.which("docker"):
            return ContainerState(
                name=name,
                status=ContainerStatus.UNKNOWN,
                port_open=False,
                is_running=False,
                details="Docker CLI not found",
            )
        try:
            inspect_cmd = ["docker", "inspect", "--format", "{{.State.Running}}", name]
            res = subprocess.run(inspect_cmd, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                return ContainerState(
                    name=name,
                    status=ContainerStatus.MISSING,
                    port_open=False,
                    is_running=False,
                    details=res.stderr.strip(),
                )
            is_running = res.stdout.strip().lower() == "true"
            status = ContainerStatus.RUNNING if is_running else ContainerStatus.STOPPED
            port_open = is_port_open(port, host=host) if port is not None else is_running
            return ContainerState(
                name=name,
                status=status,
                port_open=port_open,
                is_running=is_running,
                details="Running" if is_running else "Stopped",
            )
        except Exception as err:
            logger.debug(f"Exception checking state for container '{name}': {err}")
            return ContainerState(
                name=name,
                status=ContainerStatus.UNKNOWN,
                port_open=False,
                is_running=False,
                details=str(err),
            )

    @classmethod
    def start_existing(cls, name: str, port: Optional[int] = None, host: str = "127.0.0.1", max_retries: int = 20) -> bool:
        logger.info(f"Attempting to start stopped container '{name}'...")
        res = subprocess.run(["docker", "start", name], capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            logger.warning(f"Failed to start existing container '{name}': {res.stderr}")
            return False
        if port is None:
            return True
        for _ in range(max_retries):
            if is_port_open(port, host=host, timeout=0.3):
                logger.info(f"Container '{name}' started and port {port} is responsive.")
                return True
            _sleep_interval(0.3)
        logger.warning(f"Container '{name}' started but port {port} did not respond within timeout.")
        return False

    @classmethod
    def launch_fresh(cls, spec: ContainerSpec, max_retries: int = 30) -> bool:
        subprocess.run(["docker", "rm", "-f", spec.name], capture_output=True, text=True, timeout=15)
        cmd: list[str] = [
            "docker", "run", "-d",
            "--name", spec.name,
            "--restart", spec.restart_policy,
        ]
        if spec.network_mode == "host":
            cmd.extend(["--net", "host"])
        else:
            if spec.network_mode != "bridge":
                cmd.extend(["--net", spec.network_mode])
            if spec.port is not None:
                h_port = spec.host_port or spec.port
                cmd.extend(["-p", f"{spec.bind_ip}:{h_port}:{spec.port}"])

        for k, v in spec.environment.items():
            cmd.extend(["-e", f"{k}={v}"])

        for src, dst in spec.volumes.items():
            cmd.extend(["-v", f"{src}:{dst}"])

        cmd.append(spec.image)
        if spec.command:
            cmd.extend(shlex.split(spec.command))

        logger.info(f"Launching fresh container '{spec.name}' from image '{spec.image}'...")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            logger.warning(f"Failed to deploy container '{spec.name}': {res.stderr}")
            return False

        if spec.port is None:
            state = cls.get_state(spec.name)
            return state.is_running

        for _ in range(max_retries):
            if is_port_open(spec.port, host=spec.bind_ip, timeout=0.3):
                _sleep_interval(0.5)
                logger.info(f"Container '{spec.name}' is verified healthy on port {spec.port}.")
                return True
            _sleep_interval(0.3)

        logger.warning(f"Container '{spec.name}' launched but port {spec.port} failed to respond.")
        return False

    @classmethod
    def ensure_running(
        cls,
        spec: ContainerSpec,
        image_mgr: ImagePuller,
        on_bg_ready: Optional[Callable[[], None]] = None,
    ) -> bool:
        if spec.port is not None and is_port_open(spec.port, host=spec.bind_ip):
            return True

        state = cls.get_state(spec.name, port=spec.port, host=spec.bind_ip)
        if state.is_running and (spec.port is None or state.port_open):
            return True

        if state.status == ContainerStatus.STOPPED:
            started = cls.start_existing(spec.name, port=spec.port, host=spec.bind_ip)
            if started:
                return True
            logger.warning(f"Existing container '{spec.name}' failed to resume. Recreating...")

        if not image_mgr.is_available(spec.image):
            if spec.background_pull:
                image_mgr.pull_background(spec.image, on_complete=on_bg_ready)
                return False
            pulled = image_mgr.pull(spec.image)
            if not pulled:
                return False

        return cls.launch_fresh(spec)

    @staticmethod
    def stop(name: str, timeout: int = 5) -> bool:
        if not shutil.which("docker"):
            return False
        logger.info(f"Stopping container '{name}'...")
        try:
            res = subprocess.run(
                ["docker", "stop", "-t", str(timeout), name],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )
            return res.returncode == 0
        except Exception as err:
            logger.warning(f"Exception stopping container '{name}': {err}")
            return False

    @staticmethod
    def remove(name: str) -> bool:
        if not shutil.which("docker"):
            return False
        try:
            res = subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True, timeout=10)
            return res.returncode == 0
        except Exception as err:
            logger.warning(f"Exception removing container '{name}': {err}")
            return False
