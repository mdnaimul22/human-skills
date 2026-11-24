from __future__ import annotations

import subprocess
import threading
import time
import urllib.request
from src.config import Settings, setup_logger

logger = setup_logger(Settings.LOG_DIR / "nginx.log", name="apps.nginx.service")


class Service:
    @classmethod
    def test_syntax(cls) -> bool:
        logger.info("Validating system Nginx configuration syntax...")
        try:
            res = subprocess.run(["sudo", "nginx", "-t"], capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                logger.error(f"Nginx configuration test failed: {res.stderr}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error testing Nginx syntax: {e}")
            return False

    @classmethod
    def reload(cls) -> bool:
        logger.info("Reloading Nginx service...")
        try:
            res = subprocess.run(["sudo", "systemctl", "reload", "nginx"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                logger.info("Nginx service reloaded successfully!")
                return True
            logger.info("Reload failed, attempting restart on Nginx...")
            restart_res = subprocess.run(["sudo", "systemctl", "restart", "nginx"], capture_output=True, text=True, timeout=10)
            if restart_res.returncode == 0:
                logger.info("Nginx service restarted successfully!")
                return True
            logger.error(f"Failed to restart Nginx service: {restart_res.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error reloading Nginx: {e}")
            return False

    @classmethod
    def is_running(cls) -> bool:
        try:
            res = subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], capture_output=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def test_and_reload(cls) -> bool:
        if not cls.test_syntax():
            return False
        return cls.reload()

    @classmethod
    def probe_health(cls, timeout: float = 30.0) -> bool:
        target_host = "127.0.0.1" if Settings.API_HOST in ("0.0.0.0", "") else Settings.API_HOST
        scheme = "http"
        url = f"{scheme}://{target_host}:{Settings.API_PORT}/health"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "NginxService/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        logger.info(f"Backend health check passed ({resp.status})")
                        return True
            except Exception as err:
                logger.debug(f"Health probe waiting for backend: {err}")
            time.sleep(2.0)
        logger.warning(f"Backend health check failed ({timeout}s timeout)")
        return False

    @classmethod
    def run_delayed_probe(cls, timeout: float = 30.0, initial_delay: float = 1.0) -> None:
        if initial_delay > 0:
            time.sleep(initial_delay)
        cls.probe_health(timeout=timeout)

    @classmethod
    def start_health_probe(cls, timeout: float = 30.0, initial_delay: float = 1.0) -> None:
        threading.Thread(
            target=cls.run_delayed_probe,
            args=(timeout, initial_delay),
            daemon=True,
        ).start()
