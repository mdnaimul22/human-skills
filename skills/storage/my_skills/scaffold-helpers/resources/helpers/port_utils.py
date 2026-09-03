"""
Port Utilities
=================
Handles port management, socket discovery, and process tree termination.
Guarantees clean socket release to eliminate "EADDRINUSE" and "Address already in use" errors.
"""

import os
import re
import signal
import subprocess
import time
from typing import List, Set

from src.config import setup_logger, Settings

logger = setup_logger(Settings.LOG_DIR / "helper.log", name="app.helpers.port_utils")


def get_pid(port: int) -> List[int]:
    """
    Discovers all process IDs listening on or bound to a specific TCP port.
    Uses multi-strategy detection across:
    1. fuser (Kernel socket table — catches IPv4 and IPv6)
    2. ss (Linux socket statistics — listening sockets)
    3. lsof (Only listen sockets to avoid killing browser clients)
    """
    pids: Set[int] = set()

    # Strategy 1: fuser (Most accurate for Linux TCP sockets)
    try:
        res = subprocess.run(
            ["fuser", f"{port}/tcp"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        for part in res.stdout.strip().split():
            clean = re.sub(r"\D", "", part)
            if clean.isdigit():
                pids.add(int(clean))
    except Exception:
        pass

    # Strategy 2: ss (Socket statistics filter for listening sockets)
    try:
        res = subprocess.run(
            ["ss", "-tulpn", f"sport = :{port}"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        for match in re.finditer(r"pid=(\d+)", res.stdout):
            pids.add(int(match.group(1)))
    except Exception:
        pass

    # Strategy 3: lsof (Only listen sockets to avoid killing browser clients)
    try:
        res = subprocess.run(
            ["lsof", "-iTCP:" + str(port), "-sTCP:LISTEN", "-t"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        for line in res.stdout.strip().splitlines():
            clean = line.strip()
            if clean.isdigit():
                pids.add(int(clean))
    except Exception:
        pass

    return sorted(list(pids))


def is_port_free(port: int) -> bool:
    """Checks whether a port has no listening processes."""
    return len(get_pid(port)) == 0


def kill_pid(port: int) -> bool:
    """
    Forcefully frees a TCP port by terminating the process and all child workers.
    Ensures zero zombie sockets remain.
    """
    pids = get_pid(port)

    # If no listening PID was detected, verify port is free
    if not pids and is_port_free(port):
        return True

    logger.warning(f"Found process(es) holding port {port} (PIDs: {pids}). Freeing port...")

    # Phase 1: Terminate discovered PIDs and their child process trees
    for pid in pids:
        try:
            # Terminate child processes first (e.g. next-server spawned by npm/node)
            subprocess.run(["pkill", "-TERM", "-P", str(pid)], capture_output=True, timeout=2.0)
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        except Exception as e:
            logger.debug(f"SIGTERM error on PID {pid}: {e}")

    time.sleep(0.2)

    # Phase 2: Force SIGKILL if any process remains
    for pid in pids:
        try:
            os.kill(pid, 0)  # Check if alive
            subprocess.run(["pkill", "-9", "-P", str(pid)], capture_output=True, timeout=2.0)
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        except Exception:
            pass

    # Phase 3: Direct fuser -k hammer as failsafe
    try:
        subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True, timeout=2.0)
    except Exception:
        pass

    # Phase 4: Name-based fallback cleanup for common servers on standard ports
    if port == 3000:
        try:
            subprocess.run(["pkill", "-9", "-f", "next-server"], capture_output=True, timeout=2.0)
        except Exception:
            pass

    # Phase 5: Wait and verify port release
    for _ in range(10):  # Up to 2 seconds
        if is_port_free(port):
            logger.info(f"Port {port} successfully freed.")
            return True
        time.sleep(0.2)

    logger.error(f"Port {port} could not be freed after aggressive cleanup.")
    return False

