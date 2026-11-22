from __future__ import annotations

import shutil
import subprocess
from src.config import Settings, exists, setup_logger

logger = setup_logger(Settings.LOG_DIR / "nginx.log", name="apps.nginx.installer")


class Installer:
    @classmethod
    def is_installed(cls) -> bool:
        return shutil.which("nginx") is not None

    @classmethod
    def ensure_installed(cls) -> bool:
        if cls.is_installed():
            return True
        logger.info("Nginx binary not found. Launching auto-installation...")
        if not shutil.which("apt-get"):
            logger.error("Package manager apt-get not found on host system.")
            return False
        try:
            subprocess.run(["sudo", "apt-get", "update", "-y"], capture_output=True, timeout=120)
            res = subprocess.run(
                ["sudo", "apt-get", "install", "-y", "nginx"],
                capture_output=True, text=True, timeout=180,
            )
            if res.returncode == 0 and cls.is_installed():
                logger.info("Nginx installed successfully via apt-get.")
                return True
            logger.error(f"Failed to install Nginx via apt-get: {res.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error during Nginx auto-installation: {e}")
            return False

    @classmethod
    def ensure_dirs(cls) -> bool:
        try:
            res = subprocess.run(
                ["sudo", "mkdir", "-p", "/etc/nginx/sites-available", "/etc/nginx/sites-enabled", "/etc/nginx/snippets"],
                capture_output=True, text=True, timeout=10,
            )
            if exists("/etc/nginx/sites-enabled/default"):
                subprocess.run(["sudo", "rm", "-f", "/etc/nginx/sites-enabled/default"], capture_output=True, timeout=5)
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Failed to setup Nginx system directories: {e}")
            return False
