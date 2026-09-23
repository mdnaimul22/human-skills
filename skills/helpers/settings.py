from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .paths import PROJECT_ROOT


class Settings(BaseSettings):
    API_HOST: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")

    PIXABAY_API_KEY: Optional[str] = Field(default=None, validation_alias="PIXABAY_API_KEY")
    PIXABAY_API_URL: str = Field(default="https://pixabay.com/api/", validation_alias="PIXABAY_API_URL")
    PIXABAY_VIDEO_API_URL: str = Field(default="https://pixabay.com/api/videos/", validation_alias="PIXABAY_VIDEO_API_URL")

    PEXELS_API_KEY: Optional[str] = Field(default=None, validation_alias="PEXELS_API_KEY")
    PEXELS_API_URL: str = Field(default="https://api.pexels.com", validation_alias="PEXELS_API_URL")

    def _resolve(self, val: str) -> Path:
        val = val.strip()
        if val.startswith("/."):
            val = "~/" + val[2:] if val.startswith("/./") else "~/" + val[1:]
        if val.startswith(".") and not val.startswith("./") and not val.startswith("../"):
            val = "~/" + val
        p = Path(val).expanduser()
        return p if p.is_absolute() else PROJECT_ROOT / p

    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / ".env"),
            str(PROJECT_ROOT / ".env.others"),
            str(PROJECT_ROOT / ".env.stock_resource"),
        ),
        env_file_encoding="utf-8",
        extra="allow",
        populate_by_name=True,
    )


Settings = Settings()
