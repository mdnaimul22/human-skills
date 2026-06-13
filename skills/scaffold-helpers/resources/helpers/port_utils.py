"""
Port Utilities
=================
Handles port management and process termination.
Auto-kills orphaned server processes before startup to prevent
"Address already in use" errors.
"""

import os
import signal
import subprocess
import shlex
import time
from typing import List

from src.config import setup_logger, Settings

logger = setup_logger(Settings.LOG_DIR / "helper.log", name="app.helpers.port_utils")


def get_pid(port: int) -> List[int]:
    """Get all PIDs listening on a specific port"""
    try:
        cmd = f"lsof -t -i:{port}"
        output = subprocess.check_output(shlex.split(cmd), text=True)
        return [int(pid) for pid in output.strip().split('\n') if pid.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    except Exception as e:
        logger.error(f"Error finding PIDs on port {port}: {e}")
        return []


def kill_pid(port: int) -> bool:
    """Find and kill processes running on a specific port"""
    pids = get_pid(port)
    if not pids:
        return False

    logger.warning(f"Found {len(pids)} process(es) holding port {port} (PIDs: {pids}). Attempting cleanup...")

    success = True
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
            try:
                os.kill(pid, 0)  # Check if still alive
                os.kill(pid, signal.SIGKILL)  # Force kill
            except OSError:
                _already_dead = True
        except ProcessLookupError:
            _already_dead = True
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            success = False

    # Wait for OS to release the port
    if pids:
        for _ in range(5):  # Max 1 second
            time.sleep(0.2)
            if not get_pid(port):
                logger.info(f"Port {port} successfully freed.")
                return True

        logger.error(f"Port {port} still appears to be in use after cleanup attempt.")

    return success
