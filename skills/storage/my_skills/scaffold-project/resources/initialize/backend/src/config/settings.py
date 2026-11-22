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

    API_HOST: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")
    FRONTEND_URL: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")
    FRONTEND_PORT: int = Field(default=3000, validation_alias="FRONTEND_PORT")
    ENABLE_TAILSCALE: bool = Field(default=False, validation_alias="ENABLE_TAILSCALE")
    PUBLIC_URL: Optional[str] = Field(default=None, validation_alias="PUBLIC_URL")

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/app.db", validation_alias="DATABASE_URL")

    JWT_SECRET: str = Field(default="super-secret-key-change-me", validation_alias="JWT_SECRET")
    ACCESS_TOKEN_EXPIRY_MINUTES: int = Field(default=15, validation_alias="ACCESS_TOKEN_EXPIRY_MINUTES")
    REFRESH_TOKEN_EXPIRY_HOURS: int = Field(default=168, validation_alias="REFRESH_TOKEN_EXPIRY_HOURS")
    VERIFY_TOKEN_EXPIRY_HOURS: int = Field(default=24, validation_alias="VERIFY_TOKEN_EXPIRY_HOURS")
    RESET_TOKEN_EXPIRY_HOURS: int = Field(default=1, validation_alias="RESET_TOKEN_EXPIRY_HOURS")

    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_SECRET")

    FRONTEND_VERIFY_URL: str = Field(default="http://localhost:3000/verify-email", validation_alias="FRONTEND_VERIFY_URL")
    FRONTEND_RESET_URL: str = Field(default="http://localhost:3000/reset-password", validation_alias="FRONTEND_RESET_URL")

    NGINX_RATE_LIMIT_ZONE_SIZE: str = Field(default="10m", validation_alias="NGINX_RATE_LIMIT_ZONE_SIZE")
    NGINX_RATE_LIMIT_RATE: str = Field(default="10r/s", validation_alias="NGINX_RATE_LIMIT_RATE")
    NGINX_RATE_LIMIT_BURST: int = Field(default=20, validation_alias="NGINX_RATE_LIMIT_BURST")

    SMTP_HOST: Optional[str] = Field(default=None, validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, validation_alias="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, validation_alias="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = Field(default=None, validation_alias="SMTP_FROM_EMAIL")
    LLM_TEMPERATURE: float = Field(default=0.7, validation_alias="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=2048, validation_alias="LLM_MAX_TOKENS")
    LLM_RETRIES: int = Field(default=3, validation_alias="LLM_RETRIES")
    WEBSHARE_TOKEN: Optional[str] = Field(default=None, validation_alias="WEBSHARE_TOKEN")
    PROXY_CACHE_PATH: str = Field(default="data/proxies.json", validation_alias="PROXY_CACHE_PATH")
    PROXY_LAST_UPDATE_PATH: str = Field(default="logs/proxy_last_update.json", validation_alias="PROXY_LAST_UPDATE_PATH")
    WEBSHARE_API_URL: str = Field(
        default="https://proxy.webshare.io/api/v2/proxy/list/download/ulbftisilmdzajnvjjibaxyyyjfuphlrdogauaal/-/any/username/direct/-",
        validation_alias="WEBSHARE_API_URL",
    )

    @property
    def LOG_DIR(self) -> Path:
        return PROJECT_ROOT.safe_resolve(self.RAW_LOG_DIR)

    @property
    def DATA_DIR(self) -> Path:
        return PROJECT_ROOT.safe_resolve(self.RAW_DATA_DIR)

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "development"

    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / "env" / ".1e2n3v3"),
            str(PROJECT_ROOT / "env" / ".1g2i3t4s5y6n7c"),
            str(PROJECT_ROOT / "env" / ".1y2s3t4e5m"),
            str(PROJECT_ROOT / "env" / ".1m2o3d4e5l3s"),
        ),
        env_file_encoding="utf-8",
        extra="allow",
        populate_by_name=True,
    )


Settings = Settings()
