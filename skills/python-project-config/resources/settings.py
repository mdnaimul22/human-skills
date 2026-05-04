from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .paths import PROJECT_ROOT

class Settings(BaseSettings):
    PROJECT_NAME: str = "MyProject"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", validation_alias="APP_ENV")

    API_HOST: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")
    FRONTEND_PORT: int = Field(default=3000, validation_alias="FRONTEND_PORT")
    FRONTEND_URL: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")

    SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")

    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")
    LOCAL_DATABASE_URL: Optional[str] = None

    _LOG_DIR: str = Field(default="logs", validation_alias="LOG_DIR")
    _TOOLS_DIR: str = Field(default="core/tools", validation_alias="TOOLS_DIR")

    def _resolve(self, val: str) -> Path:
        p = Path(val).expanduser()
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def LOG_DIR(self) -> Path: return self._resolve(self._LOG_DIR)
    @property
    def TOOLS_DIR(self) -> Path: return self._resolve(self._TOOLS_DIR)
    @property
    def is_production(self) -> bool: return self.ENV.lower() == "production"
    @property
    def is_development(self) -> bool: return self.ENV.lower() == "development"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

Settings = Settings()
