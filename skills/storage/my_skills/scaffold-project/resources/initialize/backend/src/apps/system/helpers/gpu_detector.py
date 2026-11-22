from __future__ import annotations
import ctypes
import os
import re
import shutil
import subprocess
import threading
from typing import Optional
from src.config import Settings, exists, get_abs_path, is_file, setup_logger
from src.helpers import get_ffmpeg_process_env
from ..schema import GpuBackend, GpuDeviceTelemetry, GpuTelemetry

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.gpu_detector")
_DRIVER_RE = re.compile(r"[0-9]+(?:\.[0-9]+)*")
_CC_RE = re.compile(r"^\d+\.\d+$")
_NVENC_CANDIDATES: tuple[str, ...] = ("h264_nvenc", "hevc_nvenc", "av1_nvenc")
_SMI_FIELDS = "index,uuid,name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu,compute_cap"


def _decode_text(raw: bytes | str) -> str:
    match raw:
        case bytes():
            return raw.decode("utf-8", errors="replace").strip()
        case _:
            return str(raw).strip()


def _normalize_driver(raw: bytes | str) -> str:
    text = _decode_text(raw)
    match = _DRIVER_RE.search(text)
    return match.group(0) if match else "0.0"


def _normalize_cc(raw: str) -> str:
    clean = raw.strip()
    return clean if _CC_RE.match(clean) else "0.0"


def _parse_int_field(raw: str, default: int = 0) -> int:
    try:
        return int(float(raw.strip()))
    except (ValueError, TypeError):
        return default


def _parse_float_field(raw: str, default: float = 0.0) -> float:
    try:
        return float(raw.strip())
    except (ValueError, TypeError):
        return default


class GpuDetector:
    def __init__(self) -> None:
        self._nvml_lock = threading.Lock()
        self._nvml_initialized: bool = False
        self._nvml_failed: bool = False
        self._nvenc_lock = threading.Lock()
        self._nvenc_checked: bool = False
        self._nvenc_verified: bool = False
        self._nvenc_encoders: list[str] = []
        self._nvenc_failure_reason: Optional[str] = None
        self._warned_nvml_fallback: bool = False

    def _preload_nvml_libs(self) -> None:
        for raw_dir in Settings.SYSTEM_GPU_LIB_DIRS.split(","):
            lib_dir = raw_dir.strip()
            if not lib_dir:
                continue
            candidate = f"{lib_dir}/libnvidia-ml.so.1"
            if is_file(candidate):
                try:
                    ctypes.CDLL(candidate, mode=ctypes.RTLD_GLOBAL)
                    return
                except OSError as err:
                    logger.debug(f"Failed preloading NVML library from {candidate}: {err}")

    def _ensure_nvml(self) -> bool:
        if self._nvml_initialized:
            return True
        if self._nvml_failed:
            return False
        with self._nvml_lock:
            if self._nvml_initialized:
                return True
            if self._nvml_failed:
                return False
            try:
                import pynvml
            except ImportError:
                self._nvml_failed = True
                return False
            try:
                pynvml.nvmlInit()
                self._nvml_initialized = True
                return True
            except (pynvml.NVMLError, OSError):
                self._preload_nvml_libs()
                try:
                    pynvml.nvmlInit()
                    self._nvml_initialized = True
                    return True
                except (pynvml.NVMLError, OSError) as err:
                    self._nvml_failed = True
                    if not self._warned_nvml_fallback:
                        self._warned_nvml_fallback = True
                        logger.warning(f"NVML initialization unavailable, falling back to CLI probe: {err}")
                    return False

    def _probe_nvml_device(self, idx: int, driver_ver: str) -> GpuDeviceTelemetry:
        import pynvml

        handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
        name = _decode_text(pynvml.nvmlDeviceGetName(handle)) or f"NVIDIA GPU {idx}"
        try:
            dev_uuid = _decode_text(pynvml.nvmlDeviceGetUUID(handle))
        except pynvml.NVMLError:
            dev_uuid = ""
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        total_b = max(0, int(mem.total))
        free_b = min(total_b, max(0, int(mem.free))) if total_b > 0 else max(0, int(mem.free))
        used_b = min(total_b, max(0, int(mem.used))) if total_b > 0 else max(0, int(mem.used))
        try:
            major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
            cc = f"{int(major)}.{int(minor)}"
        except pynvml.NVMLError:
            cc = "0.0"
        gpu_util = 0.0
        mem_util = 0.0
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = max(0.0, min(100.0, float(util.gpu)))
            mem_util = max(0.0, min(100.0, float(util.memory)))
        except pynvml.NVMLError as err:
            logger.debug(f"NVML utilization unavailable for gpu={idx}: {err}")
        temp_c = 0
        try:
            temp_c = max(0, int(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)))
        except pynvml.NVMLError as err:
            logger.debug(f"NVML temperature unavailable for gpu={idx}: {err}")
        enc_util = 0.0
        try:
            raw_enc = pynvml.nvmlDeviceGetEncoderUtilization(handle)
            if raw_enc:
                enc_util = max(0.0, min(100.0, float(raw_enc[0])))
        except pynvml.NVMLError as err:
            logger.debug(f"NVML encoder utilization unavailable for gpu={idx}: {err}")
        active_sessions = 0
        try:
            enc_stats = pynvml.nvmlDeviceGetEncoderStats(handle)
            if enc_stats:
                active_sessions = max(0, int(enc_stats[0]))
        except pynvml.NVMLError as err:
            logger.debug(f"NVML encoder stats unavailable for gpu={idx}: {err}")
        return GpuDeviceTelemetry(
            device_id=idx,
            uuid=dev_uuid,
            name=name,
            total_vram_bytes=total_b,
            free_vram_bytes=free_b,
            used_vram_bytes=used_b,
            compute_capability=cc,
            driver_version=driver_ver,
            gpu_util_percent=gpu_util,
            mem_util_percent=mem_util,
            temperature_c=temp_c,
            encoder_util_percent=enc_util,
            active_nvenc_sessions=active_sessions,
        )

    def _probe_nvml(self) -> Optional[GpuTelemetry]:
        if not self._ensure_nvml():
            return None
        try:
            import pynvml

            count = int(pynvml.nvmlDeviceGetCount())
            if count <= 0:
                return None
            driver_ver = _normalize_driver(pynvml.nvmlSystemGetDriverVersion())
            devices = [self._probe_nvml_device(i, driver_ver) for i in range(count)]
            primary = devices[0]
            return GpuTelemetry(
                device_id=primary.device_id,
                name=primary.name,
                total_vram_bytes=primary.total_vram_bytes,
                free_vram_bytes=primary.free_vram_bytes,
                compute_capability=primary.compute_capability,
                driver_version=driver_ver,
                cuda_available=True,
                device_count=len(devices),
                devices=devices,
                backend=GpuBackend.NVML,
            )
        except Exception as exc:
            logger.warning(f"NVML telemetry query failed, falling back to nvidia-smi: {exc}")
            return None

    def _resolve_nvidia_smi(self) -> Optional[str]:
        found = shutil.which("nvidia-smi")
        if found:
            return found
        candidates = [d.strip() for d in Settings.SYSTEM_GPU_LIB_DIRS.split(",") if d.strip()]
        candidates.extend(["/usr/bin", "/usr/local/bin"])
        for d in candidates:
            path = f"{d}/nvidia-smi"
            if is_file(path):
                return path
        return None

    def _probe_nvidia_smi(self) -> Optional[GpuTelemetry]:
        smi_bin = self._resolve_nvidia_smi()
        if not smi_bin:
            return None
        try:
            proc = subprocess.run(
                [smi_bin, f"--query-gpu={_SMI_FIELDS}", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                env=get_ffmpeg_process_env(),
                timeout=Settings.SYSTEM_GPU_PROBE_TIMEOUT_SEC,
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                return None
            devices: list[GpuDeviceTelemetry] = []
            for row in proc.stdout.strip().splitlines():
                cols = [c.strip() for c in row.split(",")]
                if len(cols) < 11:
                    continue
                idx = _parse_int_field(cols[0], len(devices))
                dev_uuid = cols[1] if cols[1] != "[N/A]" else ""
                name = cols[2] or f"NVIDIA GPU {idx}"
                driver_ver = _normalize_driver(cols[3])
                total_b = max(0, _parse_int_field(cols[4]) * 1024 * 1024)
                used_b = min(total_b, max(0, _parse_int_field(cols[5]) * 1024 * 1024))
                free_b = min(total_b, max(0, _parse_int_field(cols[6]) * 1024 * 1024))
                gpu_util = max(0.0, min(100.0, _parse_float_field(cols[7])))
                mem_util = max(0.0, min(100.0, _parse_float_field(cols[8])))
                temp_c = max(0, _parse_int_field(cols[9]))
                cc = _normalize_cc(cols[10])
                devices.append(
                    GpuDeviceTelemetry(
                        device_id=idx,
                        uuid=dev_uuid,
                        name=name,
                        total_vram_bytes=total_b,
                        free_vram_bytes=free_b,
                        used_vram_bytes=used_b,
                        compute_capability=cc,
                        driver_version=driver_ver,
                        gpu_util_percent=gpu_util,
                        mem_util_percent=mem_util,
                        temperature_c=temp_c,
                    )
                )
            if not devices:
                return None
            primary = devices[0]
            return GpuTelemetry(
                device_id=primary.device_id,
                name=primary.name,
                total_vram_bytes=primary.total_vram_bytes,
                free_vram_bytes=primary.free_vram_bytes,
                compute_capability=primary.compute_capability,
                driver_version=primary.driver_version,
                cuda_available=True,
                device_count=len(devices),
                devices=devices,
                backend=GpuBackend.NVIDIA_SMI,
            )
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            logger.warning(f"nvidia-smi fallback probe failed: {exc}")
            return None

    def _probe_vaapi(self) -> GpuTelemetry:
        vaapi_dev = Settings.FFMPEG_VAAPI_DEVICE.strip()
        vaapi_ok = bool(vaapi_dev and exists(vaapi_dev) and os.access(vaapi_dev, os.R_OK | os.W_OK))
        return GpuTelemetry(
            backend=GpuBackend.VAAPI if vaapi_ok else GpuBackend.NONE,
            cuda_available=False,
            device_count=1 if vaapi_ok else 0,
            vaapi_available=vaapi_ok,
            unavailable_reason=None if vaapi_ok else "No NVIDIA GPU or accessible VAAPI render node detected",
        )

    def _resolve_ffmpeg_bin(self) -> Optional[str]:
        managed = get_abs_path(f"{Settings.FFMPEG_BIN_DIR}/ffmpeg")
        if is_file(managed) and os.access(managed, os.X_OK):
            return managed
        return shutil.which("ffmpeg")

    def probe_nvenc_capabilities(self, force: bool = False) -> tuple[bool, list[str], Optional[str]]:
        with self._nvenc_lock:
            if self._nvenc_checked and not force:
                return self._nvenc_verified, list(self._nvenc_encoders), self._nvenc_failure_reason
            ffmpeg_bin = self._resolve_ffmpeg_bin()
            if not ffmpeg_bin:
                self._nvenc_checked = True
                self._nvenc_verified = False
                self._nvenc_encoders = []
                self._nvenc_failure_reason = "FFmpeg binary unavailable for NVENC canary"
                return False, [], self._nvenc_failure_reason

            env = get_ffmpeg_process_env()
            timeout = Settings.SYSTEM_GPU_CANARY_TIMEOUT_SEC
            try:
                enc_proc = subprocess.run(
                    [ffmpeg_bin, "-hide_banner", "-encoders"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=timeout,
                )
                enc_out = enc_proc.stdout
                found_encoders = [name for name in _NVENC_CANDIDATES if re.search(rf"\b{name}\b", enc_out)]
                if "h264_nvenc" not in found_encoders:
                    self._nvenc_checked = True
                    self._nvenc_verified = False
                    self._nvenc_encoders = found_encoders
                    self._nvenc_failure_reason = "FFmpeg build lacks h264_nvenc encoder"
                    return False, list(found_encoders), self._nvenc_failure_reason

                canary_proc = subprocess.run(
                    [
                        ffmpeg_bin, "-hide_banner", "-loglevel", "error",
                        "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.04",
                        "-frames:v", "1", "-c:v", "h264_nvenc", "-f", "null", "-",
                    ],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=timeout,
                )
                if canary_proc.returncode != 0:
                    err_msg = (canary_proc.stderr or canary_proc.stdout).strip()[:240] or f"exit={canary_proc.returncode}"
                    self._nvenc_checked = True
                    self._nvenc_verified = False
                    self._nvenc_encoders = found_encoders
                    self._nvenc_failure_reason = f"NVENC canary failed: {err_msg}"
                    return False, list(found_encoders), self._nvenc_failure_reason

                self._nvenc_checked = True
                self._nvenc_verified = True
                self._nvenc_encoders = found_encoders
                self._nvenc_failure_reason = None
                return True, list(found_encoders), None
            except (OSError, subprocess.TimeoutExpired) as exc:
                self._nvenc_checked = True
                self._nvenc_verified = False
                self._nvenc_encoders = []
                self._nvenc_failure_reason = f"NVENC canary error: {exc}"
                return False, [], self._nvenc_failure_reason

    def sample(self, include_nvenc_check: bool = True, force_capability_recheck: bool = False) -> GpuTelemetry:
        if not Settings.SYSTEM_GPU_ENABLED:
            return GpuTelemetry(
                backend=GpuBackend.NONE,
                cuda_available=False,
                device_count=0,
                unavailable_reason="GPU disabled via SYSTEM_GPU_ENABLED=false",
            )
        gpu = self._probe_nvml() or self._probe_nvidia_smi()
        if gpu is None:
            return self._probe_vaapi()
        if include_nvenc_check:
            verified, encoders, reason = self.probe_nvenc_capabilities(force=force_capability_recheck)
            gpu.nvenc_verified = verified
            gpu.nvenc_encoders = encoders
            gpu.nvenc_failure_reason = reason
        return gpu

    def shutdown(self) -> None:
        with self._nvml_lock:
            if not self._nvml_initialized:
                return
            try:
                import pynvml
                pynvml.nvmlShutdown()
            except Exception as err:
                logger.debug(f"NVML shutdown ignored error: {err}")
            finally:
                self._nvml_initialized = False
