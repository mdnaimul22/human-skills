import os
import uuid
import pytest
from pydantic import ValidationError as PydanticValidationError
from src.config import Settings, delete, get_abs_path, is_dir, write_text
from src.helpers import get_ffmpeg_process_env, inject_gpu_library_env


def test_system_settings_90_percent_defaults() -> None:
    assert Settings.SYSTEM_CONFIG_FILE == "env/.system"
    assert Settings.SYSTEM_MAX_CPU_USAGE_PERCENT == 90.0
    assert Settings.SYSTEM_MAX_RAM_USAGE_PERCENT == 90.0
    assert Settings.SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT == 90.0
    assert Settings.SYSTEM_GPU_MAX_UTIL_PERCENT == 90.0
    assert Settings.SYSTEM_GPU_MAX_NVENC_SESSIONS >= 1
    assert Settings.SYSTEM_TELEMETRY_POLL_INTERVAL_SEC == 2.0


def test_reload_system_env_atomic_validation_and_apply() -> None:
    rel_cfg = f"tmp/test_tmp/system_cfg_{os.getpid()}_{uuid.uuid4().hex[:6]}.env"
    orig_cfg_file = Settings.SYSTEM_CONFIG_FILE
    orig_cpu = Settings.SYSTEM_MAX_CPU_USAGE_PERCENT
    orig_nvenc = Settings.SYSTEM_GPU_MAX_NVENC_SESSIONS
    orig_env_cpu = os.environ.get("SYSTEM_MAX_CPU_USAGE_PERCENT")
    orig_env_nvenc = os.environ.get("SYSTEM_GPU_MAX_NVENC_SESSIONS")
    try:
        Settings.SYSTEM_CONFIG_FILE = rel_cfg
        write_text(rel_cfg, "SYSTEM_MAX_CPU_USAGE_PERCENT=78.5\nSYSTEM_GPU_MAX_NVENC_SESSIONS=5\n")
        changes = Settings.reload_system_env()
        assert changes["SYSTEM_MAX_CPU_USAGE_PERCENT"] == (orig_cpu, 78.5)
        assert changes["SYSTEM_GPU_MAX_NVENC_SESSIONS"] == (orig_nvenc, 5)
        assert Settings.SYSTEM_MAX_CPU_USAGE_PERCENT == 78.5
        assert Settings.SYSTEM_GPU_MAX_NVENC_SESSIONS == 5

        write_text(
            rel_cfg,
            "SYSTEM_MAX_CPU_USAGE_PERCENT=65.0\nSYSTEM_CPU_ELEVATED_PCT=90.0\nSYSTEM_CPU_CRITICAL_PCT=80.0\n",
        )
        with pytest.raises(PydanticValidationError):
            Settings.reload_system_env()
        assert Settings.SYSTEM_MAX_CPU_USAGE_PERCENT == 78.5
        assert Settings.SYSTEM_CPU_ELEVATED_PCT < Settings.SYSTEM_CPU_CRITICAL_PCT
    finally:
        Settings.SYSTEM_CONFIG_FILE = orig_cfg_file
        Settings.SYSTEM_MAX_CPU_USAGE_PERCENT = orig_cpu
        Settings.SYSTEM_GPU_MAX_NVENC_SESSIONS = orig_nvenc
        if orig_env_cpu is None:
            os.environ.pop("SYSTEM_MAX_CPU_USAGE_PERCENT", None)
        else:
            os.environ["SYSTEM_MAX_CPU_USAGE_PERCENT"] = orig_env_cpu
        if orig_env_nvenc is None:
            os.environ.pop("SYSTEM_GPU_MAX_NVENC_SESSIONS", None)
        else:
            os.environ["SYSTEM_GPU_MAX_NVENC_SESSIONS"] = orig_env_nvenc
        delete(rel_cfg)


def test_inject_gpu_library_env_idempotent_and_preserves_ld_path(monkeypatch: pytest.MonkeyPatch) -> None:
    rel_existing = f"tmp/test_tmp/gpu_lib_{os.getpid()}_{uuid.uuid4().hex[:6]}"
    abs_existing = get_abs_path(rel_existing)
    abs_missing = get_abs_path(f"{rel_existing}_missing")
    os.makedirs(abs_existing, exist_ok=True)
    try:
        monkeypatch.setattr(Settings, "SYSTEM_GPU_LIB_DIRS", f"{abs_existing}, {abs_missing}")
        assert is_dir(abs_existing)
        assert not is_dir(abs_missing)

        env_empty: dict[str, str] = {}
        inject_gpu_library_env(env_empty)
        assert env_empty["LD_LIBRARY_PATH"] == abs_existing

        env_existing = {"LD_LIBRARY_PATH": "/custom/lib:/opt/cuda/lib64"}
        inject_gpu_library_env(env_existing)
        assert env_existing["LD_LIBRARY_PATH"] == f"{abs_existing}:/custom/lib:/opt/cuda/lib64"

        inject_gpu_library_env(env_existing)
        assert env_existing["LD_LIBRARY_PATH"] == f"{abs_existing}:/custom/lib:/opt/cuda/lib64"
    finally:
        if os.path.isdir(abs_existing):
            os.rmdir(abs_existing)


def test_get_ffmpeg_process_env_strips_secrets_and_injects_gpu_libs(monkeypatch: pytest.MonkeyPatch) -> None:
    rel_existing = f"tmp/test_tmp/ffmpeg_gpu_lib_{os.getpid()}_{uuid.uuid4().hex[:6]}"
    abs_existing = get_abs_path(rel_existing)
    os.makedirs(abs_existing, exist_ok=True)
    try:
        monkeypatch.setenv("JWT_SECRET", "super-secret")
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9999")
        monkeypatch.setattr(Settings, "SYSTEM_GPU_LIB_DIRS", abs_existing)
        env = get_ffmpeg_process_env(proxy_url="http://127.0.0.1:20001")
        assert "JWT_SECRET" not in env
        assert env["HTTP_PROXY"] == "http://127.0.0.1:20001"
        assert abs_existing in env["LD_LIBRARY_PATH"].split(":")
    finally:
        if os.path.isdir(abs_existing):
            os.rmdir(abs_existing)
