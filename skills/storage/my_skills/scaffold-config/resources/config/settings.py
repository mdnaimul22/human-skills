from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .paths import PROJECT_ROOT


class Settings(BaseSettings):
    PROJECT_NAME: str = "MyProject"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", validation_alias="APP_ENV")

    RAW_LOG_DIR: str = Field(default="logs", validation_alias="LOG_DIR")
    RAW_DATA_DIR: str = Field(default="data", validation_alias="DATA_DIR")

    # --- Server ---
    API_HOST: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")
    FRONTEND_URL: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")

    # --- Database ---
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/app.db", validation_alias="DATABASE_URL")

    # --- Auth ---
    JWT_SECRET: str = Field(default="super-secret-key-change-me", validation_alias="JWT_SECRET")
    JWT_EXPIRY_HOURS: int = Field(default=168, validation_alias="JWT_EXPIRY_HOURS")

    # --- Nginx Rate Limiting ---
    NGINX_RATE_LIMIT_ZONE_SIZE: str = Field(default="10m", validation_alias="NGINX_RATE_LIMIT_ZONE_SIZE")
    NGINX_RATE_LIMIT_RATE: str = Field(default="10r/s", validation_alias="NGINX_RATE_LIMIT_RATE")
    NGINX_RATE_LIMIT_BURST: int = Field(default=20, validation_alias="NGINX_RATE_LIMIT_BURST")


    def _resolve(self, val: str) -> Path:
        
        val = val.strip()
        # Handle /.hidden -> ~/.hidden (Forgotten tilde)
        if val.startswith("/."):
            val = "~/" + val[2:] if val.startswith("/./") else "~/" + val[1:]

        
        # Handle .hidden (if it's not ./ or ../) -> treat as home relative for our tools
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
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


Settings = Settings()