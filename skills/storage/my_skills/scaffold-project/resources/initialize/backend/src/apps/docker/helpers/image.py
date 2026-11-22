from __future__ import annotations
import shutil
import subprocess
import threading
from typing import Callable, Optional
from src.config import Settings, setup_logger

logger = setup_logger(Settings.LOG_DIR / "docker.log", name="apps.docker.image")

class ImagePuller:
    def __init__(self) -> None:
        self._pulling_images: set[str] = set()
        self._lock = threading.Lock()

    def is_available(self, image: str) -> bool:
        if not shutil.which("docker"):
            return False
        try:
            res = subprocess.run(
                ["docker", "image", "inspect", image],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return res.returncode == 0
        except Exception as err:
            logger.debug(f"Docker image inspect failed for '{image}': {err}")
            return False

    def is_pulling(self, image: str) -> bool:
        with self._lock:
            return image in self._pulling_images

    def pull(self, image: str, timeout: int = 180) -> bool:
        if self.is_available(image):
            return True
        logger.info(f"Downloading Docker image '{image}' synchronously. Please wait...")
        try:
            res = subprocess.run(
                ["docker", "pull", image],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if res.returncode == 0:
                logger.info(f"Docker image '{image}' downloaded successfully.")
                return True
            logger.warning(f"Failed to pull Docker image '{image}': {res.stderr}")
            return False
        except Exception as err:
            logger.error(f"Error during Docker pull for '{image}': {err}")
            return False

    def pull_background(self, image: str, on_complete: Optional[Callable[[], None]] = None) -> None:
        with self._lock:
            if image in self._pulling_images:
                logger.info(f"Docker image '{image}' pull is already in progress.")
                return
            self._pulling_images.add(image)

        logger.info(f"Initiating background Docker image download for '{image}'.")
        thread = threading.Thread(
            target=self._run_background_pull,
            args=(image, on_complete),
            daemon=True,
        )
        thread.start()

    def _run_background_pull(self, image: str, on_complete: Optional[Callable[[], None]]) -> None:
        try:
            res = subprocess.run(
                ["docker", "pull", image],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                logger.info(f"Background pull for Docker image '{image}' succeeded.")
                if on_complete:
                    on_complete()
            else:
                logger.warning(f"Background pull for Docker image '{image}' failed: {res.stderr}")
        except Exception as err:
            logger.error(f"Exception during background Docker image pull for '{image}': {err}")
        finally:
            with self._lock:
                self._pulling_images.discard(image)
