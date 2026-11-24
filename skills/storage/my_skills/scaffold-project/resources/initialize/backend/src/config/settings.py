from pathlib import Path
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .paths import PROJECT_ROOT


class Settings(BaseSettings):
    PROJECT_NAME: str = "MyProject"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", validation_alias="APP_ENV")

    RAW_LOG_DIR: str = Field(default="logs", validation_alias="LOG_DIR")
    RAW_DATA_DIR: str = Field(default="data", validation_alias="DATA_DIR")
    RAW_TEMP_DIR: str = Field(default="tmp", validation_alias="TEMP_DIR")

    API_HOST: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")
    FRONTEND_URL: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")
    FRONTEND_PORT: int = Field(default=3000, validation_alias="FRONTEND_PORT")
    BACKEND_DOMAIN: str = Field(default="127.0.0.1", validation_alias="BACKEND_DOMAIN")
    FRONTEND_DOMAIN: str = Field(default="localhost", validation_alias="FRONTEND_DOMAIN")
    EXTRA_CORS_ORIGINS: str = Field(default="", validation_alias="EXTRA_CORS_ORIGINS")
    ALLOWED_REDIRECT_HOSTS: str = Field(default="", validation_alias="ALLOWED_REDIRECT_HOSTS")
    PUBLIC_URL: Optional[str] = Field(default=None, validation_alias="PUBLIC_URL")
    SSL_EMAIL: str = Field(default="", validation_alias="SSL_EMAIL")
    GOOGLE_VERIFICATION_CODE: str = Field(default="", validation_alias="GOOGLE_VERIFICATION_CODE")

    TUNNEL_CONFIG_FILE: str = Field(default="env/.1t2u3n4n5e6l7", validation_alias="TUNNEL_CONFIG_FILE")
    TUNNEL_MANAGER: bool = Field(default=False, validation_alias="TUNNEL_MANAGER")
    TUNNEL: bool = Field(default=False, validation_alias="TUNNEL")
    TUNNEL_PROVIDER: str = Field(default="cloudflared", validation_alias="TUNNEL_PROVIDER")
    TUNNEL_TARGET_HOST: str = Field(default="127.0.0.1", validation_alias="TUNNEL_TARGET_HOST")
    TUNNEL_TARGET_PORT: int = Field(default=0, ge=0, le=65535, validation_alias="TUNNEL_TARGET_PORT")
    TUNNEL_AUTO_INSTALL: bool = Field(default=True, validation_alias="TUNNEL_AUTO_INSTALL")
    TUNNEL_AUTO_RESTART: bool = Field(default=True, validation_alias="TUNNEL_AUTO_RESTART")
    TUNNEL_POLL_INTERVAL_SEC: float = Field(default=5.0, ge=0.5, le=300.0, validation_alias="TUNNEL_POLL_INTERVAL_SEC")
    TUNNEL_START_TIMEOUT_SEC: float = Field(default=45.0, ge=5.0, le=600.0, validation_alias="TUNNEL_START_TIMEOUT_SEC")
    TUNNEL_MAX_RESTARTS: int = Field(default=5, ge=0, le=50, validation_alias="TUNNEL_MAX_RESTARTS")
    TUNNEL_CLOUDFLARE_TOKEN: str = Field(default="", validation_alias="TUNNEL_CLOUDFLARE_TOKEN")
    TUNNEL_CLOUDFLARE_HOSTNAME: str = Field(default="", validation_alias="TUNNEL_CLOUDFLARE_HOSTNAME")
    TUNNEL_TAILSCALE_AUTHKEY: str = Field(default="", validation_alias="TUNNEL_TAILSCALE_AUTHKEY")
    TUNNEL_TAILSCALE_HTTPS_PORT: int = Field(default=443, ge=1, le=65535, validation_alias="TUNNEL_TAILSCALE_HTTPS_PORT")

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/app.db", validation_alias="DATABASE_URL")
    REDIS_ENABLED: bool = Field(default=False, validation_alias="REDIS_ENABLED")
    REDIS_URL: str = Field(default="redis://127.0.0.1:6379/0", validation_alias="REDIS_URL")
    REDIS_MAX_CONNECTIONS: int = Field(default=20, validation_alias="REDIS_MAX_CONNECTIONS")

    JWT_SECRET: str = Field(default="super-secret-key-change-me", validation_alias="JWT_SECRET")
    JWT_EXPIRY_HOURS: int = Field(default=24, validation_alias="JWT_EXPIRY_HOURS")
    ACCESS_TOKEN_EXPIRY_MINUTES: int = Field(default=15, validation_alias="ACCESS_TOKEN_EXPIRY_MINUTES")
    REFRESH_TOKEN_EXPIRY_HOURS: int = Field(default=168, validation_alias="REFRESH_TOKEN_EXPIRY_HOURS")
    VERIFY_TOKEN_EXPIRY_HOURS: int = Field(default=24, validation_alias="VERIFY_TOKEN_EXPIRY_HOURS")
    RESET_TOKEN_EXPIRY_HOURS: int = Field(default=1, validation_alias="RESET_TOKEN_EXPIRY_HOURS")

    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/api/v1/auth/callback", validation_alias="GOOGLE_REDIRECT_URI")

    FRONTEND_VERIFY_URL: str = Field(default="http://localhost:3000/verify-email", validation_alias="FRONTEND_VERIFY_URL")
    FRONTEND_RESET_URL: str = Field(default="http://localhost:3000/reset-password", validation_alias="FRONTEND_RESET_URL")

    NGINX_RATE_LIMIT_ZONE_SIZE: str = Field(default="10m", validation_alias="NGINX_RATE_LIMIT_ZONE_SIZE")
    NGINX_RATE_LIMIT_RATE: str = Field(default="10r/s", validation_alias="NGINX_RATE_LIMIT_RATE")
    NGINX_RATE_LIMIT_BURST: int = Field(default=20, validation_alias="NGINX_RATE_LIMIT_BURST")
    NGINX_ENABLE_HTTP2: bool = Field(default=True, validation_alias="NGINX_ENABLE_HTTP2")

    SMTP_HOST: Optional[str] = Field(default=None, validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, validation_alias="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, validation_alias="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = Field(default=None, validation_alias="SMTP_FROM_EMAIL")

    LLM_TEMPERATURE: float = Field(default=0.7, validation_alias="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=2048, validation_alias="LLM_MAX_TOKENS")
    LLM_RETRIES: int = Field(default=3, validation_alias="LLM_RETRIES")

    PROXY_CONFIG_FILE: str = Field(default="env/.1p2r3o4x5y6", validation_alias="PROXY_CONFIG_FILE")
    PROXY_MANAGER: bool = Field(default=False, validation_alias="PROXY_MANAGER")
    PROXY: bool = Field(default=False, validation_alias="PROXY")
    PROXY_PROVIDER: str = Field(default="webshare", validation_alias="PROXY_PROVIDER")
    PROXY_CACHE_PATH: str = Field(default="data/providers/proxy/proxies.json", validation_alias="PROXY_CACHE_PATH")
    PROXY_STATE_PATH: str = Field(default="data/providers/proxy/state.json", validation_alias="PROXY_STATE_PATH")
    PROXY_REFRESH_INTERVAL_SEC: float = Field(default=3600.0, ge=10.0, le=86400.0, validation_alias="PROXY_REFRESH_INTERVAL_SEC")
    PROXY_POLL_INTERVAL_SEC: float = Field(default=30.0, ge=0.5, le=300.0, validation_alias="PROXY_POLL_INTERVAL_SEC")
    PROXY_REQUEST_TIMEOUT_SEC: float = Field(default=30.0, ge=1.0, le=120.0, validation_alias="PROXY_REQUEST_TIMEOUT_SEC")
    PROXY_COOLDOWN_SEC: float = Field(default=120.0, ge=1.0, le=3600.0, validation_alias="PROXY_COOLDOWN_SEC")
    PROXY_MAX_FAILURES: int = Field(default=3, ge=1, le=20, validation_alias="PROXY_MAX_FAILURES")
    PROXY_STATIC_URLS: str = Field(default="", validation_alias="PROXY_STATIC_URLS")
    WEBSHARE_TOKEN: str = Field(default="", validation_alias="WEBSHARE_TOKEN")
    WEBSHARE_API_URL: str = Field(default="", validation_alias="WEBSHARE_API_URL")

    MAX_CONCURRENT_JOBS: int = Field(default=20, validation_alias="MAX_CONCURRENT_JOBS")
    MAX_USER_CONCURRENT_JOBS: int = Field(default=15, validation_alias="MAX_USER_CONCURRENT_JOBS")
    MAX_ACTIVE_JOBS_PER_IP: int = Field(default=5, validation_alias="MAX_ACTIVE_JOBS_PER_IP")
    MAX_QUEUE_DEPTH: int = Field(default=50, validation_alias="MAX_QUEUE_DEPTH")
    MAX_CONCURRENT_DOWNLOADS: int = Field(default=10, validation_alias="MAX_CONCURRENT_DOWNLOADS")
    MAX_CONCURRENT_ENCODES: int = Field(default=2, validation_alias="MAX_CONCURRENT_ENCODES")
    MAX_CONCURRENT_LIGHT_ENCODES: int = Field(default=4, validation_alias="MAX_CONCURRENT_LIGHT_ENCODES")
    MAX_CONCURRENT_ANALYSIS: int = Field(default=4, validation_alias="MAX_CONCURRENT_ANALYSIS")
    MAX_FILE_SIZE_MB: int = Field(default=512, validation_alias="MAX_FILE_SIZE_MB")
    JOB_MAX_RUNTIME: int = Field(default=1800, validation_alias="JOB_MAX_RUNTIME")
    TEMP_FILE_TTL_SECONDS: int = Field(default=3600, validation_alias="TEMP_FILE_TTL_SECONDS")
    GUEST_FILE_TTL: int = Field(default=1800, validation_alias="GUEST_FILE_TTL")
    REGISTERED_FILE_TTL: int = Field(default=7200, validation_alias="REGISTERED_FILE_TTL")
    PREMIUM_FILE_TTL: int = Field(default=86400, validation_alias="PREMIUM_FILE_TTL")

    GITSYNC_ENABLED: bool = Field(default=False, validation_alias="GITSYNC_ENABLED")
    RAW_GITSYNC_DATA_DIR: str = Field(default="data/apps/git", validation_alias="GITSYNC_DATA_DIR")
    GITSYNC_PROJECTS_FILE: str = Field(default="projects.json", validation_alias="GITSYNC_PROJECTS_FILE")
    GITSYNC_AUTOMATION_FILE: str = Field(default="automation.json", validation_alias="GITSYNC_AUTOMATION_FILE")
    GITSYNC_FORWARD_FILE: str = Field(default="forward.json", validation_alias="GITSYNC_FORWARD_FILE")
    GITSYNC_UPSTREAM_FILE: str = Field(default="upstream.json", validation_alias="GITSYNC_UPSTREAM_FILE")
    GITSYNC_MEMORY_FILE: str = Field(default="memory.json", validation_alias="GITSYNC_MEMORY_FILE")
    GIT_AUTO_COMMIT: bool = Field(default=False, validation_alias="GIT_AUTO_COMMIT")
    GIT_AUTO_PUSH: bool = Field(default=False, validation_alias="GIT_AUTO_PUSH")
    GIT_BRANCH: str = Field(default="main", validation_alias="GIT_BRANCH")
    GIT_TIMEOUT_SECONDS: int = Field(default=60, validation_alias="GIT_TIMEOUT_SECONDS")
    SYNC_INTERVAL_MINUTES: int = Field(default=30, validation_alias="SYNC_INTERVAL_MINUTES")
    SYNC_POLL_SECONDS: int = Field(default=10, validation_alias="SYNC_POLL_SECONDS")

    FFMPEG_BIN_DIR: str = Field(default="", validation_alias="FFMPEG_BIN_DIR")
    FFMPEG_VAAPI_DEVICE: str = Field(default="/dev/dri/renderD128", validation_alias="FFMPEG_VAAPI_DEVICE")

    SYSTEM_CONFIG_FILE: str = Field(default="env/.1y2s3t4e5m", validation_alias="SYSTEM_CONFIG_FILE")
    SYSTEM_TELEMETRY_POLL_INTERVAL_SEC: float = Field(default=2.0, ge=0.5, le=30.0, validation_alias="SYSTEM_TELEMETRY_POLL_INTERVAL_SEC")
    SYSTEM_TELEMETRY_CACHE_TTL_SEC: float = Field(default=2.0, ge=0.1, le=30.0, validation_alias="SYSTEM_TELEMETRY_CACHE_TTL_SEC")
    SYSTEM_HEARTBEAT_INTERVAL_SEC: float = Field(default=60.0, ge=5.0, le=600.0, validation_alias="SYSTEM_HEARTBEAT_INTERVAL_SEC")
    SYSTEM_REAPER_INTERVAL_SEC: float = Field(default=30.0, ge=1.0, le=600.0, validation_alias="SYSTEM_REAPER_INTERVAL_SEC")
    SYSTEM_DEFAULT_LEASE_TTL_SEC: float = Field(default=300.0, ge=10.0, le=7200.0, validation_alias="SYSTEM_DEFAULT_LEASE_TTL_SEC")
    SYSTEM_CPU_EWMA_ALPHA: float = Field(default=0.4, gt=0.0, le=1.0, validation_alias="SYSTEM_CPU_EWMA_ALPHA")
    SYSTEM_LOAD_RECOVERY_STREAK: int = Field(default=3, ge=1, le=20, validation_alias="SYSTEM_LOAD_RECOVERY_STREAK")
    SYSTEM_LOAD_HYSTERESIS_PCT: float = Field(default=5.0, ge=0.0, le=20.0, validation_alias="SYSTEM_LOAD_HYSTERESIS_PCT")

    SYSTEM_MAX_CPU_USAGE_PERCENT: float = Field(default=90.0, ge=10.0, le=100.0, validation_alias="SYSTEM_MAX_CPU_USAGE_PERCENT")
    SYSTEM_RESERVED_CPU_CORES: int = Field(default=1, ge=0, le=64, validation_alias="SYSTEM_RESERVED_CPU_CORES")
    SYSTEM_MAX_RAM_USAGE_PERCENT: float = Field(default=90.0, ge=10.0, le=100.0, validation_alias="SYSTEM_MAX_RAM_USAGE_PERCENT")
    SYSTEM_MIN_FREE_RAM_MB: int = Field(default=1024, ge=64, validation_alias="SYSTEM_MIN_FREE_RAM_MB")

    SYSTEM_CPU_ELEVATED_PCT: float = Field(default=75.0, ge=10.0, le=99.0, validation_alias="SYSTEM_CPU_ELEVATED_PCT")
    SYSTEM_CPU_CRITICAL_PCT: float = Field(default=88.0, ge=20.0, le=99.5, validation_alias="SYSTEM_CPU_CRITICAL_PCT")
    SYSTEM_CPU_EMERGENCY_PCT: float = Field(default=95.0, ge=30.0, le=100.0, validation_alias="SYSTEM_CPU_EMERGENCY_PCT")
    SYSTEM_RAM_ELEVATED_PCT: float = Field(default=80.0, ge=10.0, le=99.0, validation_alias="SYSTEM_RAM_ELEVATED_PCT")
    SYSTEM_RAM_CRITICAL_PCT: float = Field(default=90.0, ge=20.0, le=99.5, validation_alias="SYSTEM_RAM_CRITICAL_PCT")
    SYSTEM_RAM_EMERGENCY_PCT: float = Field(default=95.0, ge=30.0, le=100.0, validation_alias="SYSTEM_RAM_EMERGENCY_PCT")
    SYSTEM_RAM_ELEVATED_FREE_MB: int = Field(default=1536, ge=128, validation_alias="SYSTEM_RAM_ELEVATED_FREE_MB")
    SYSTEM_RAM_CRITICAL_FREE_MB: int = Field(default=768, ge=64, validation_alias="SYSTEM_RAM_CRITICAL_FREE_MB")
    SYSTEM_RAM_EMERGENCY_FREE_MB: int = Field(default=384, ge=32, validation_alias="SYSTEM_RAM_EMERGENCY_FREE_MB")

    SYSTEM_GPU_ENABLED: bool = Field(default=True, validation_alias="SYSTEM_GPU_ENABLED")
    SYSTEM_GPU_LIB_DIRS: str = Field(default="/usr/lib/wsl/lib", validation_alias="SYSTEM_GPU_LIB_DIRS")
    SYSTEM_GPU_PROBE_TIMEOUT_SEC: float = Field(default=2.0, ge=0.5, le=30.0, validation_alias="SYSTEM_GPU_PROBE_TIMEOUT_SEC")
    SYSTEM_GPU_CANARY_TIMEOUT_SEC: float = Field(default=3.0, ge=0.5, le=30.0, validation_alias="SYSTEM_GPU_CANARY_TIMEOUT_SEC")
    SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT: float = Field(default=90.0, ge=10.0, le=100.0, validation_alias="SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT")
    SYSTEM_GPU_MIN_FREE_VRAM_MB: int = Field(default=512, ge=64, validation_alias="SYSTEM_GPU_MIN_FREE_VRAM_MB")
    SYSTEM_GPU_MAX_TEMP_C: int = Field(default=83, ge=40, le=110, validation_alias="SYSTEM_GPU_MAX_TEMP_C")
    SYSTEM_GPU_MAX_UTIL_PERCENT: float = Field(default=90.0, ge=10.0, le=100.0, validation_alias="SYSTEM_GPU_MAX_UTIL_PERCENT")
    SYSTEM_GPU_MAX_NVENC_SESSIONS: int = Field(default=3, ge=1, le=32, validation_alias="SYSTEM_GPU_MAX_NVENC_SESSIONS")
    SYSTEM_GPU_ENCODE_CPU_THREADS: int = Field(default=2, ge=1, le=32, validation_alias="SYSTEM_GPU_ENCODE_CPU_THREADS")
    SYSTEM_GPU_ENCODE_VRAM_MB: int = Field(default=512, ge=64, validation_alias="SYSTEM_GPU_ENCODE_VRAM_MB")
    SYSTEM_GPU_ML_VRAM_MB: int = Field(default=1536, ge=128, validation_alias="SYSTEM_GPU_ML_VRAM_MB")

    SYSTEM_MAX_RENDER_SLOTS: int = Field(default=4, ge=1, validation_alias="SYSTEM_MAX_RENDER_SLOTS")
    SYSTEM_MAX_AUDIO_SLOTS: int = Field(default=4, ge=1, validation_alias="SYSTEM_MAX_AUDIO_SLOTS")
    SYSTEM_MAX_ML_SLOTS: int = Field(default=2, ge=1, validation_alias="SYSTEM_MAX_ML_SLOTS")
    SYSTEM_ENCODE_MAX_THREADS: int = Field(default=8, ge=1, validation_alias="SYSTEM_ENCODE_MAX_THREADS")
    SYSTEM_RENDER_MAX_THREADS: int = Field(default=6, ge=1, validation_alias="SYSTEM_RENDER_MAX_THREADS")
    SYSTEM_TIER_GUEST_CPU_RATIO: float = Field(default=0.50, gt=0.0, le=1.0, validation_alias="SYSTEM_TIER_GUEST_CPU_RATIO")
    SYSTEM_TIER_REGISTERED_CPU_RATIO: float = Field(default=0.75, gt=0.0, le=1.0, validation_alias="SYSTEM_TIER_REGISTERED_CPU_RATIO")
    SYSTEM_TIER_PREMIUM_CPU_RATIO: float = Field(default=1.00, gt=0.0, le=1.0, validation_alias="SYSTEM_TIER_PREMIUM_CPU_RATIO")
    SYSTEM_TIER_GUEST_RAM_MB: int = Field(default=256, ge=64, validation_alias="SYSTEM_TIER_GUEST_RAM_MB")
    SYSTEM_TIER_REGISTERED_RAM_MB: int = Field(default=512, ge=64, validation_alias="SYSTEM_TIER_REGISTERED_RAM_MB")
    SYSTEM_TIER_PREMIUM_RAM_MB: int = Field(default=2048, ge=128, validation_alias="SYSTEM_TIER_PREMIUM_RAM_MB")
    SYSTEM_GPU_ALLOWED_TIERS: str = Field(default="registered,premium", validation_alias="SYSTEM_GPU_ALLOWED_TIERS")

    SYSTEM_BREAKER_FAILURE_THRESHOLD: int = Field(default=3, ge=1, validation_alias="SYSTEM_BREAKER_FAILURE_THRESHOLD")
    SYSTEM_BREAKER_COOLDOWN_SEC: float = Field(default=600.0, ge=1.0, validation_alias="SYSTEM_BREAKER_COOLDOWN_SEC")
    SYSTEM_BREAKER_HALF_OPEN_TIMEOUT_SEC: float = Field(default=15.0, ge=1.0, validation_alias="SYSTEM_BREAKER_HALF_OPEN_TIMEOUT_SEC")

    @model_validator(mode="after")
    def validate_system_thresholds(self) -> "Settings":
        if not (self.SYSTEM_CPU_ELEVATED_PCT < self.SYSTEM_CPU_CRITICAL_PCT < self.SYSTEM_CPU_EMERGENCY_PCT):
            raise ValueError("CPU pressure thresholds must strictly ascend (ELEVATED < CRITICAL < EMERGENCY)")
        if not (self.SYSTEM_RAM_ELEVATED_PCT < self.SYSTEM_RAM_CRITICAL_PCT < self.SYSTEM_RAM_EMERGENCY_PCT):
            raise ValueError("RAM pressure thresholds must strictly ascend (ELEVATED < CRITICAL < EMERGENCY)")
        if not (self.SYSTEM_RAM_ELEVATED_FREE_MB > self.SYSTEM_RAM_CRITICAL_FREE_MB > self.SYSTEM_RAM_EMERGENCY_FREE_MB):
            raise ValueError("RAM free floors must strictly descend (ELEVATED > CRITICAL > EMERGENCY)")
        return self

    @property
    def resolved_tunnel_port(self) -> int:
        return self.TUNNEL_TARGET_PORT if self.TUNNEL_TARGET_PORT > 0 else self.API_PORT

    @property
    def LOG_DIR(self) -> Path:
        return PROJECT_ROOT.safe_resolve(self.RAW_LOG_DIR)

    @property
    def DATA_DIR(self) -> Path:
        return PROJECT_ROOT.safe_resolve(self.RAW_DATA_DIR)

    @property
    def TEMP_DIR(self) -> Path:
        return PROJECT_ROOT.safe_resolve(self.RAW_TEMP_DIR)

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "development"

    @property
    def is_testing(self) -> bool:
        return self.ENV.lower() == "testing"

    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / "env" / ".1e2n3v3"),
            str(PROJECT_ROOT / "env" / ".1g2i3t4s5y6n7c"),
            str(PROJECT_ROOT / "env" / ".1y2s3t4e5m"),
            str(PROJECT_ROOT / "env" / ".1m2o3d4e5l3s"),
            str(PROJECT_ROOT / "env" / ".1t2u3n4n5e6l7"),
            str(PROJECT_ROOT / "env" / ".1p2r3o4x5y6"),
        ),
        env_file_encoding="utf-8",
        extra="allow",
        populate_by_name=True,
    )


Settings = Settings()
