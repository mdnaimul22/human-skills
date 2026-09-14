"""
Frontend process orchestrator.
Manages the Next.js frontend lifecycle concurrently with the FastAPI backend.
"""
import os
import signal
import subprocess
import sys
from typing import Optional

from src.config import Settings, setup_logger, exists, get_abs_path
from src.helpers.port_utils import kill_pid

logger = setup_logger(Settings.LOG_DIR / "helper.log", name="app.helpers.frontend")


def get_frontend_port() -> int:
    return Settings.FRONTEND_PORT


def ensure_production_build() -> bool:
    web_abs_path = get_abs_path("web")

    if not exists("web/.next"):
        logger.info("Next.js production build not found in web/.next. Running 'npm run build'...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=web_abs_path,
            capture_output=False
        )
        if result.returncode != 0:
            logger.error("Failed to build Next.js production bundle")
            return False
        logger.info("Next.js production build completed successfully")
    return True


class FrontendManager:
    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None

    def start(self) -> Optional[subprocess.Popen]:
        web_abs_path = get_abs_path("web")
        port = get_frontend_port()

        kill_pid(port)

        is_prod = Settings.is_production
        mode = "production" if is_prod else "development"

        logger.info(f"Starting Next.js frontend in {mode} mode on port {port}...")

        if is_prod:
            ensure_production_build()
            cmd = ["npm", "run", "start", "--", "-p", str(port)]
        else:
            cmd = ["npm", "run", "dev", "--", "-p", str(port)]

        try:
            env_vars = dict(os.environ)
            env_vars["PORT"] = str(port)
            preexec_fn = os.setsid if sys.platform != "win32" else None
            self.proc = subprocess.Popen(
                cmd,
                cwd=web_abs_path,
                env=env_vars,
                preexec_fn=preexec_fn
            )
            return self.proc
        except Exception as e:
            logger.error(f"Failed to start frontend process: {e}")
            return None

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            logger.info("Shutting down frontend process group...")
            try:
                if sys.platform != "win32":
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
                else:
                    self.proc.terminate()

                self.proc.wait(timeout=3)
            except Exception as e:
                logger.debug(f"SIGTERM exception during frontend shutdown: {e}")
                try:
                    if sys.platform != "win32":
                        os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                    else:
                        self.proc.kill()
                except Exception as e2:
                    logger.debug(f"SIGKILL exception during frontend shutdown: {e2}")
            finally:
                self.proc = None
                port = get_frontend_port()
                kill_pid(port)


frontend_manager = FrontendManager()
start_frontend = frontend_manager.start
stop_frontend = frontend_manager.stop
