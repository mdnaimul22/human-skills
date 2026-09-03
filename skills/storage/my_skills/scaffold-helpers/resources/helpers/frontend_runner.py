"""
Frontend process orchestrator.
Manages the Next.js frontend lifecycle concurrently with the FastAPI backend.
"""
import os
import signal
import subprocess
from typing import Optional
from urllib.parse import urlparse

from src.config import Settings, setup_logger, exists, get_abs_path
from src.helpers.port_utils import kill_pid

logger = setup_logger(Settings.LOG_DIR / "helper.log", name="app.helpers.frontend")

_frontend_proc: Optional[subprocess.Popen] = None


def get_frontend_port() -> int:
    """Extracts frontend port from Settings.FRONTEND_URL or defaults to 3000."""
    try:
        parsed = urlparse(Settings.FRONTEND_URL)
        return parsed.port or 3000
    except Exception:
        return 3000


def ensure_production_build() -> bool:
    """Ensures Next.js production build (.next) exists; triggers build if missing."""
    web_abs_path = get_abs_path("web")

    if not exists("web/.next"):
        logger.info("Next.js production build not found in web/.next. Running 'npm run build'...")
        print("📦 [Build] Generating optimized Next.js production bundle...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=web_abs_path,
            capture_output=False
        )
        if result.returncode != 0:
            logger.error("Failed to build Next.js production bundle")
            print("❌ [Build] Next.js build failed!")
            return False
        logger.info("Next.js production build completed successfully")
        print("✅ [Build] Production bundle ready.")
    return True


def start_frontend() -> Optional[subprocess.Popen]:
    """
    Launches Next.js frontend process in development or production mode
    based on Settings.ENV.
    """
    global _frontend_proc
    web_abs_path = get_abs_path("web")
    port = get_frontend_port()

    # Free the frontend port from any orphaned processes
    kill_pid(port)

    is_prod = Settings.is_production
    mode = "production" if is_prod else "development"

    logger.info(f"Starting Next.js frontend in {mode} mode on port {port}...")
    print(f"🚀 [Frontend] Starting Next.js ({mode} mode) on http://localhost:{port}...")

    if is_prod:
        ensure_production_build()
        cmd = ["npm", "run", "start", "--", "-p", str(port)]
    else:
        cmd = ["npm", "run", "dev", "--", "-p", str(port)]

    try:
        _frontend_proc = subprocess.Popen(
            cmd,
            cwd=web_abs_path,
            env=dict(os.environ, PORT=str(port)),
            # Use process group so terminating kills all child node workers
            preexec_fn=os.setsid if hasattr(os, "setsid") else None
        )
        return _frontend_proc
    except Exception as e:
        logger.error(f"Failed to start frontend process: {e}")
        print(f"❌ [Frontend] Failed to start: {e}")
        return None


def stop_frontend():
    """Cleanly terminates the frontend process group and frees the port."""
    global _frontend_proc
    if _frontend_proc and _frontend_proc.poll() is None:
        logger.info("Shutting down frontend process group...")
        print("\n🛑 [Frontend] Stopping Next.js server...")
        try:
            if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                os.killpg(os.getpgid(_frontend_proc.pid), signal.SIGTERM)
            else:
                _frontend_proc.terminate()

            _frontend_proc.wait(timeout=3)
        except Exception:
            try:
                if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                    os.killpg(os.getpgid(_frontend_proc.pid), signal.SIGKILL)
                else:
                    _frontend_proc.kill()
            except Exception:
                pass
        finally:
            _frontend_proc = None
            port = get_frontend_port()
            kill_pid(port)
