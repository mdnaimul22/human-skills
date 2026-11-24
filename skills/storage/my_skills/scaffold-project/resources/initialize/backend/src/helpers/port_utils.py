import os
import signal
import subprocess
import shlex
import time
from typing import List

from src.config import setup_logger, Settings

logger = setup_logger(Settings.LOG_DIR / "helpers.log", name="helpers.port_utils")


def get_pid(port: int) -> List[int]:
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
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                logger.debug(f"Process {pid} exited cleanly after SIGTERM")
        except ProcessLookupError:
            logger.debug(f"Process {pid} exited before signal dispatch")
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            success = False

    if pids:
        for _ in range(5):
            time.sleep(0.2)
            if not get_pid(port):
                logger.info(f"Port {port} successfully freed.")
                return True

        logger.error(f"Port {port} still appears to be in use after cleanup attempt.")

    return success
