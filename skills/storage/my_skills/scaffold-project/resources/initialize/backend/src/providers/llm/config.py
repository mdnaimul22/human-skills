import threading
from typing import Optional
from pydantic import BaseModel
from src.config import Settings
from src.helpers.exceptions import ExternalServiceError


class ClientConfig(BaseModel):
    base_url: str
    api_key: str
    model: str
    proxy: Optional[str] = None


def parse_configs(data: dict[str, str | int | float | bool | None]) -> list[ClientConfig]:
    grouped: dict[str, dict[str, str]] = {}
    for key, val in data.items():
        k = key.lower()
        if not k.startswith("client_configs_") or val is None:
            continue
        parts = k.split("_", 3)
        if len(parts) >= 4:
            idx, field_name = parts[2], parts[3]
            grouped.setdefault(idx, {})[field_name] = str(val)

    clients: list[ClientConfig] = []
    for _, item in sorted(grouped.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        base_url = item.get("base_url")
        api_key = item.get("api_key")
        model = item.get("model")
        if base_url and api_key and model:
            clients.append(
                ClientConfig(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    proxy=item.get("proxy_http") or None,
                )
            )
    return clients


def load_configs() -> list[ClientConfig]:
    return parse_configs(Settings.model_dump())


class ClientRotator:
    def __init__(self):
        self.client_configs = load_configs()
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

    def get_by_index(self, index: int) -> ClientConfig:
        if not self.client_configs:
            raise ExternalServiceError("LLM", "No client configurations available")
        if index < 0 or index >= len(self.client_configs):
            raise ExternalServiceError("LLM", f"Client index {index} out of range (total: {len(self.client_configs)})")
        return self.client_configs[index]

    def get_configs_for_model(self, model: str) -> list[ClientConfig]:
        return [c for c in self.client_configs if c.model == model]

    def get_available_models(self) -> list[str]:
        return list(dict.fromkeys(c.model for c in self.client_configs))
