from __future__ import annotations
import threading
from typing import Callable, Optional
from src.config import Settings, exists, read_json, setup_logger, write_json
from .helpers import (
    ContainerSpec,
    ContainerState,
    CONTAINER_SPECS_ADAPTER,
    ContainerEngine,
    ImagePuller,
    Installer,
)

logger = setup_logger(Settings.LOG_DIR / "docker.log", name="apps.docker.manager")

_CONFIG_PATH = "data/apps/docker/containers.json"

class DockerManager:
    _instance: Optional[DockerManager] = None
    _initialized: bool = False

    def __new__(cls) -> DockerManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = _CONFIG_PATH) -> None:
        if self._initialized:
            return
        self._config_path = config_path
        self._installer = Installer()
        self._images = ImagePuller()
        self._engine = ContainerEngine()
        self._specs: dict[str, ContainerSpec] = {}
        self._started_by_us: set[str] = set()
        self._lock = threading.Lock()
        self.reload_specs()
        self._initialized = True
        logger.info(f"DockerManager initialized with {len(self._specs)} declared container spec(s)")

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None
        cls._initialized = False

    def reload_specs(self) -> None:
        with self._lock:
            if not exists(self._config_path):
                try:
                    write_json(self._config_path, [])
                    logger.info(f"Initialized empty containers config file '{self._config_path}'.")
                except Exception as err:
                    logger.warning(f"Failed to initialize containers config '{self._config_path}': {err}")
                self._specs = {}
                return
            try:
                raw_data = read_json(self._config_path)
                spec_list = CONTAINER_SPECS_ADAPTER.validate_python(raw_data)
                self._specs = {spec.name: spec for spec in spec_list if spec.enabled}
                logger.debug(f"Loaded {len(self._specs)} container specifications.")
            except Exception as err:
                logger.error(f"Failed to parse containers config '{self._config_path}': {err}")

    def get_spec(self, name: str) -> Optional[ContainerSpec]:
        with self._lock:
            return self._specs.get(name)

    def is_docker_ready(self) -> bool:
        return self._installer.is_docker_ready()

    @staticmethod
    def is_docker_available() -> bool:
        return Installer.is_docker_ready()

    def is_image_available(self, image: str) -> bool:
        return self._images.is_available(image)

    def trigger_background_pull(self, image: str, on_complete: Optional[Callable[[], None]] = None) -> None:
        self._images.pull_background(image, on_complete=on_complete)

    def ensure_running(self, name: str) -> bool:
        spec = self.get_spec(name)
        if spec is None:
            logger.warning(f"No container specification found for '{name}'.")
            return False

        if not self._installer.ensure_ready():
            logger.warning("Docker host engine is not available.")
            return False

        def on_image_ready() -> None:
            self.ensure_running(name)

        success = self._engine.ensure_running(spec, self._images, on_bg_ready=on_image_ready)
        if success:
            with self._lock:
                self._started_by_us.add(name)
        return success

    def ensure_all(self) -> dict[str, bool]:
        with self._lock:
            active_names = list(self._specs.keys())
        results: dict[str, bool] = {}
        for name in active_names:
            success = self.ensure_running(name)
            results[name] = success
            if success:
                logger.info(f"Container '{name}' verified active and responsive.")
            else:
                logger.warning(f"Container '{name}' failed to reach active state.")
        return results

    def stop_container(self, name: str, timeout: int = 5) -> bool:
        stopped = self._engine.stop(name, timeout=timeout)
        if stopped:
            with self._lock:
                self._started_by_us.discard(name)
        return stopped

    def stop_all(self) -> None:
        with self._lock:
            to_stop = list(self._started_by_us)
        for name in to_stop:
            self.stop_container(name)
        logger.info("All Docker managed containers stopped.")

    def get_status(self, name: str) -> ContainerState:
        spec = self.get_spec(name)
        port = spec.port if spec else None
        return self._engine.get_state(name, port=port)

def get_docker_manager() -> DockerManager:
    return DockerManager()
