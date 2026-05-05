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

    # ── LLM ────────────────────────────────────────────────────────────────
    LLM_BASE_URL: str = Field(..., validation_alias="LLM_BASE_URL")
    LLM_MODEL: str = Field(
        default="CohereForAI_C4AI_Command",
        validation_alias="LLM_MODEL",
    )
    LLM_API_KEY: str = Field(default="no_key_need", validation_alias="LLM_API_KEY")
    LLM_TEMPERATURE: float = Field(default=0.3, validation_alias="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=4000, validation_alias="LLM_MAX_TOKENS")

    # ── Paths (resolved via _resolve — no hardcoding) ──────────────────────
    RAW_BRAIN_DIR: str = Field(..., validation_alias="BRAIN_DIR")
    RAW_KNOWLEDGE_DIR: str = Field(..., validation_alias="KNOWLEDGE_DIR")

    @property
    def BRAIN_DIR(self) -> Path:
        return self._resolve(self.RAW_BRAIN_DIR)

    @property
    def KNOWLEDGE_DIR(self) -> Path:
        return self._resolve(self.RAW_KNOWLEDGE_DIR)

    @property
    def STATE_FILE(self) -> Path:
        return self.DATA_DIR / "state.json"

    @property
    def PROMPTS_DIR(self) -> Path:
        return PROJECT_ROOT / "prompts"

    # ── Watcher ─────────────────────────────────────────────────────────────
    WATCHER_ENABLED: bool = Field(default=True, validation_alias="WATCHER_ENABLED")
    WATCHER_BUFFER_TURNS: int = Field(default=6, validation_alias="WATCHER_BUFFER_TURNS")
    WATCHER_BUFFER_TIMEOUT: int = Field(default=180, validation_alias="WATCHER_BUFFER_TIMEOUT")
    WATCHER_POLL_SECONDS: int = Field(default=30, validation_alias="WATCHER_POLL_SECONDS")

    # ── Batch ────────────────────────────────────────────────────────────────
    BATCH_MAX_CHARS: int = Field(default=500000, validation_alias="BATCH_MAX_CHARS")
    BATCH_CHUNK_SIZE: int = Field(default=16000, validation_alias="BATCH_CHUNK_SIZE")

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


Settings = Settings()