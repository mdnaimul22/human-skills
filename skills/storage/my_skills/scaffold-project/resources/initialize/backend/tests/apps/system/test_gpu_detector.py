from __future__ import annotations
import subprocess
import sys
import pytest
from src.apps.system import GpuBackend
from src.apps.system.helpers import GpuDetector
from src.config import Settings


def test_live_gpu_detector_uses_nvml_and_nvenc_without_torch() -> None:
    detector = GpuDetector()
    try:
        gpu = detector.sample(include_nvenc_check=True, force_capability_recheck=True)
        assert "torch" not in sys.modules
        assert gpu.backend == GpuBackend.NVML
        assert gpu.cuda_available is True
        assert gpu.device_count >= 1
        assert gpu.total_vram_bytes > 0
        assert gpu.free_vram_bytes <= gpu.total_vram_bytes
        assert gpu.driver_version != "0.0"
        assert gpu.nvenc_verified is True
        assert gpu.is_usable is True
        assert "h264_nvenc" in gpu.nvenc_encoders
    finally:
        detector.shutdown()


def test_gpu_detector_disabled_via_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Settings, "SYSTEM_GPU_ENABLED", False)
    detector = GpuDetector()
    gpu = detector.sample()
    assert gpu.backend == GpuBackend.NONE
    assert gpu.cuda_available is False
    assert gpu.is_available is False
    assert gpu.is_usable is False
    assert "SYSTEM_GPU_ENABLED=false" in (gpu.unavailable_reason or "")


def test_gpu_detector_nvidia_smi_fallback_handles_na(monkeypatch: pytest.MonkeyPatch) -> None:
    detector = GpuDetector()
    monkeypatch.setattr(detector, "_probe_nvml", lambda: None)
    monkeypatch.setattr(detector, "_resolve_nvidia_smi", lambda: "/usr/bin/nvidia-smi")

    smi_csv = "0, GPU-abc, NVIDIA RTX 3070 Ti, 610.88, 8192, 5500, 2692, [N/A], 1, 50, 8.6\n"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if any("query-gpu" in a for a in cmd):
            return subprocess.CompletedProcess(cmd, 0, stdout=smi_csv, stderr="")
        if "-encoders" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=" V....D h264_nvenc\n", stderr="")
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="No capable devices found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(detector, "_resolve_ffmpeg_bin", lambda: "/usr/bin/ffmpeg")

    gpu = detector.sample(include_nvenc_check=True, force_capability_recheck=True)
    assert gpu.backend == GpuBackend.NVIDIA_SMI
    assert gpu.cuda_available is True
    assert gpu.devices[0].gpu_util_percent == 0.0
    assert gpu.devices[0].temperature_c == 50
    assert gpu.nvenc_verified is False
    assert gpu.is_available is True
    assert gpu.is_usable is False
    assert "NVENC canary failed" in (gpu.nvenc_failure_reason or "")
    assert len(calls) >= 2


def test_gpu_detector_falls_back_to_vaapi_and_none(monkeypatch: pytest.MonkeyPatch) -> None:
    detector = GpuDetector()
    monkeypatch.setattr(detector, "_probe_nvml", lambda: None)
    monkeypatch.setattr(detector, "_probe_nvidia_smi", lambda: None)
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.sys_exists", lambda _p: False)

    gpu_none = detector.sample()
    assert gpu_none.backend == GpuBackend.NONE
    assert gpu_none.vaapi_available is False
    assert gpu_none.unavailable_reason is not None

    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.sys_exists", lambda _p: True)
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.os.access", lambda _p, _m: True)
    gpu_vaapi = detector.sample()
    assert gpu_vaapi.backend == GpuBackend.VAAPI
    assert gpu_vaapi.vaapi_available is True
    assert gpu_vaapi.cuda_available is False
    assert gpu_vaapi.is_available is True
    assert gpu_vaapi.is_usable is True


def test_gpu_detector_reads_vaapi_drm_sysfs_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    detector = GpuDetector()
    monkeypatch.setattr(detector, "_probe_nvml", lambda: None)
    monkeypatch.setattr(detector, "_probe_nvidia_smi", lambda: None)
    monkeypatch.setattr(Settings, "FFMPEG_VAAPI_DEVICE", "/dev/dri/renderD128")
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.sys_exists", lambda p: p == "/dev/dri/renderD128")
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.os.access", lambda _p, _m: True)

    dev_dir = "/sys/class/drm/renderD128/device"
    files = {
        f"{dev_dir}/vendor": "0x1002\n",
        f"{dev_dir}/uevent": "DRIVER=amdgpu\nPCI_SLOT_NAME=0000:04:00.0\n",
        f"{dev_dir}/mem_info_vram_total": str(2048 * 1024 * 1024),
        f"{dev_dir}/mem_info_vram_used": str(512 * 1024 * 1024),
        f"{dev_dir}/gpu_busy_percent": "23\n",
        f"{dev_dir}/hwmon/hwmon4/temp1_input": "64000\n",
    }
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.sys_is_dir", lambda p: p == dev_dir)
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.sys_is_file", lambda p: p in files)
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.sys_read_text", lambda p: files[p])
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.sys_list_dir", lambda p: ["hwmon4"] if p == f"{dev_dir}/hwmon" else [])
    monkeypatch.setattr("src.apps.system.helpers.gpu_detector.shutil.which", lambda _name: None)

    gpu = detector.sample()
    assert gpu.backend == GpuBackend.VAAPI
    assert gpu.name == "AMD Radeon GPU"
    assert gpu.total_vram_bytes == 2048 * 1024 * 1024
    assert gpu.free_vram_bytes == 1536 * 1024 * 1024
    assert gpu.devices[0].gpu_util_percent == 23.0
    assert gpu.devices[0].temperature_c == 64
    assert gpu.devices[0].mem_util_percent == 25.0
