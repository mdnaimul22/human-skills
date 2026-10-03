import threading
from typing import Optional
from src.config import Settings, ClientConfig
from src.helpers.exceptions import ExternalServiceError


class ClientRotator:
    def __init__(self):
        self.client_configs = Settings.LLM_CLIENTS
        self.current_index = 0
        self.model_indices: dict[str, int] = {}
        self.lock = threading.Lock()

    def get_next_client_config(self, model: Optional[str] = None) -> ClientConfig:
        with self.lock:
            if not self.client_configs:
                raise ExternalServiceError("LLM", "No client configurations available")

            if model:
                matched = [c for c in self.client_configs if c.model == model]
                if matched:
                    idx = self.model_indices.get(model, 0)
                    config = matched[idx % len(matched)]
                    self.model_indices[model] = (idx + 1) % len(matched)
                    return config

            config = self.client_configs[self.current_index % len(self.client_configs)]
            self.current_index = (self.current_index + 1) % len(self.client_configs)
            return config

    def get_configs_for_model(self, model: str) -> list[ClientConfig]:
        return [c for c in self.client_configs if c.model == model]

    def get_available_models(self) -> list[str]:
        return list(dict.fromkeys(c.model for c in self.client_configs))