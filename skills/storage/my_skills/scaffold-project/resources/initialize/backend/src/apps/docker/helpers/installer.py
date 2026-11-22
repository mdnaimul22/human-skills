from __future__ import annotations
import shutil
import subprocess
from src.config import Settings, setup_logger

logger = setup_logger(Settings.LOG_DIR / "docker.log", name="apps.docker.installer")

class Installer:
    @staticmethod
    def is_installed() -> bool:
        return shutil.which("docker") is not None

    @staticmethod
    def is_daemon_running() -> bool:
        if not shutil.which("docker"):
            return False
        try:
            res = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return res.returncode == 0
        except Exception as err:
            logger.debug(f"Docker daemon probe exception: {err}")
            return False

    @classmethod
    def is_docker_ready(cls) -> bool:
        return cls.is_installed() and cls.is_daemon_running()

    @classmethod
    def ensure_daemon_running(cls) -> bool:
        if cls.is_daemon_running():
            return True
        if not cls.is_installed():
            logger.warning("Docker CLI is not installed on host machine.")
            return False
        logger.info("Attempting to start Docker daemon service...")
        for cmd in (["systemctl", "start", "docker"], ["service", "docker", "start"]):
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if res.returncode == 0 and cls.is_daemon_running():
                    logger.info("Successfully started Docker daemon service.")
                    return True
            except Exception as err:
                logger.debug(f"Command '{cmd[0]}' failed: {err}")
        return cls.is_daemon_running()

    @classmethod
    def install_docker(cls) -> bool:
        if cls.is_docker_ready():
            return True
        logger.info("Initiating non-interactive Docker engine automated installation...")
        try:
            install_cmd = ["curl", "-fsSL", "https://get.docker.com"]
            get_sh = subprocess.Popen(install_cmd, stdout=subprocess.PIPE)
            sh_exec = subprocess.run(["sh"], stdin=get_sh.stdout, capture_output=True, text=True, timeout=300)
            if sh_exec.returncode == 0 and cls.ensure_daemon_running():
                logger.info("Docker engine installed and daemon started successfully.")
                return True
            logger.warning(f"Automated Docker installation script failed: {sh_exec.stderr}")
            return False
        except Exception as err:
            logger.error(f"Failed to install Docker engine: {err}")
            return False

    @classmethod
    def ensure_ready(cls, auto_install: bool = False) -> bool:
        if cls.is_docker_ready():
            return True
        if cls.is_installed():
            return cls.ensure_daemon_running()
        if auto_install:
            return cls.install_docker()
        logger.warning("Docker is not installed and auto_install is disabled.")
        return False
