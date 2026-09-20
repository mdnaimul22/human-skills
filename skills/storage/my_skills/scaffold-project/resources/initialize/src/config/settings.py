from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .paths import PROJECT_ROOT


class ClientConfig(BaseModel):
    base_url: str
    api_key: str
    model: str
    proxy: Optional[str] = None


class Settings(BaseSettings):
    PROJECT_NAME: str = "MyProject"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", validation_alias="APP_ENV")

    RAW_LOG_DIR: str = Field(default="logs", validation_alias="LOG_DIR")
    RAW_DATA_DIR: str = Field(default="data", validation_alias="DATA_DIR")

    API_HOST: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")
    FRONTEND_URL: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")
    FRONTEND_PORT: int = Field(default=3000, validation_alias="FRONTEND_PORT")

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/app.db", validation_alias="DATABASE_URL")

    JWT_SECRET: str = Field(default="super-secret-key-change-me", validation_alias="JWT_SECRET")
    JWT_EXPIRY_HOURS: int = Field(default=168, validation_alias="JWT_EXPIRY_HOURS")

    NGINX_RATE_LIMIT_ZONE_SIZE: str = Field(default="10m", validation_alias="NGINX_RATE_LIMIT_ZONE_SIZE")
    NGINX_RATE_LIMIT_RATE: str = Field(default="10r/s", validation_alias="NGINX_RATE_LIMIT_RATE")
    NGINX_RATE_LIMIT_BURST: int = Field(default=20, validation_alias="NGINX_RATE_LIMIT_BURST")

    SMTP_HOST: Optional[str] = Field(default=None, validation_alias="SMTP_HOST")
    LLM_TEMPERATURE: float = Field(default=0.7, validation_alias="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=2048, validation_alias="LLM_MAX_TOKENS")
    LLM_RETRIES: int = Field(default=3, validation_alias="LLM_RETRIES")
    LLM_CLIENTS: list[ClientConfig] = Field(default_factory=list)
    WEBSHARE_TOKEN: Optional[str] = Field(default=None, validation_alias="WEBSHARE_TOKEN")
    PROXY_CACHE_PATH: str = Field(default="data/proxies.json", validation_alias="PROXY_CACHE_PATH")
    PROXY_LAST_UPDATE_PATH: str = Field(default="logs/proxy_last_update.json", validation_alias="PROXY_LAST_UPDATE_PATH")
    WEBSHARE_API_URL: str = Field(
        default="https://proxy.webshare.io/api/v2/proxy/list/download/ulbftisilmdzajnvjjibaxyyyjfuphlrdogauaal/-/any/username/direct/-",
        validation_alias="WEBSHARE_API_URL",
    )
    SHOT_PLANS_DIR: str = Field(default="data/shot_plans", validation_alias="SHOT_PLANS_DIR")

    @model_validator(mode="before")
    @classmethod
    def assemble_client_configs(cls, values: dict) -> dict:
        grouped: dict[str, dict[str, str]] = {}
        for key, val in values.items():
            k = key.lower()
            if not k.startswith("client_configs_"):
                continue
            parts = k.split("_", 3)
            if len(parts) >= 4:
                idx, field_name = parts[2], parts[3]
                grouped.setdefault(idx, {})[field_name] = str(val)

        clients: list[ClientConfig] = []
        for _, data in sorted(grouped.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            base_url = data.get("base_url")
            api_key = data.get("api_key")
            model = data.get("model")
            if base_url and api_key and model:
                clients.append(
                    ClientConfig(
                        base_url=base_url,
                        api_key=api_key,
                        model=model,
                        proxy=data.get("proxy_http"),
                    )
                )

        values["LLM_CLIENTS"] = clients
        return values

    def _resolve(self, val: str) -> Path:
        val = val.strip()
        if val.startswith("/."):
            val = "~/" + val[2:] if val.startswith("/./") else "~/" + val[1:]
        if val.startswith(".") and not val.startswith("./") and not val.startswith("../"):
            val = "~/" + val
        p = Path(val).expanduser()
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def LOG_DIR(self) -> Path:
        return self._resolve(self.RAW_LOG_DIR)

    @property
    def DATA_DIR(self) -> Path:
        return self._resolve(self.RAW_DATA_DIR)

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "development"

    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / ".env"),
            str(PROJECT_ROOT / ".models"),
        ),
        env_file_encoding="utf-8",
        extra="allow",
        populate_by_name=True,
    )


Settings = Settings()
