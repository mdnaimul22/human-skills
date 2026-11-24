from __future__ import annotations
import threading
from typing import Optional
from src.config import Settings, setup_logger
from ..schema import (
    CpuTelemetry,
    GpuHealthState,
    GpuTelemetry,
    HardwareTelemetrySnapshot,
    LoadLevel,
    RamTelemetry,
)
from .circuit_breaker import HardwareCircuitBreaker

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.profiler")


class HardwareProfiler:
    def __init__(
        self,
        min_ram_available_mb: Optional[int] = None,
        ram_throttle_percent: Optional[float] = None,
        cpu_high_threshold: Optional[float] = None,
    ) -> None:
        self._explicit_min_ram = min_ram_available_mb
        self._explicit_ram_pct = ram_throttle_percent
        self._explicit_cpu_pct = cpu_high_threshold
        self._lock = threading.Lock()
        self._current_level: LoadLevel = LoadLevel.NORMAL
        self._cool_streak: int = 0
        self._last_reason: str = "healthy"

    @property
    def min_ram_available_mb(self) -> int:
        if self._explicit_min_ram is not None:
            return self._explicit_min_ram
        return Settings.SYSTEM_MIN_FREE_RAM_MB

    @property
    def ram_throttle_percent(self) -> float:
        if self._explicit_ram_pct is not None:
            return self._explicit_ram_pct
        return Settings.SYSTEM_RAM_CRITICAL_PCT

    @property
    def cpu_high_threshold(self) -> float:
        if self._explicit_cpu_pct is not None:
            return self._explicit_cpu_pct
        return Settings.SYSTEM_CPU_CRITICAL_PCT

    def is_cpu_saturated(self, cpu: CpuTelemetry) -> bool:
        return cpu.load_percent >= self.cpu_high_threshold

    def is_memory_pressured(self, ram: RamTelemetry) -> bool:
        min_ram_bytes = self.min_ram_available_mb * 1024 * 1024
        if ram.available_bytes < min_ram_bytes:
            return True
        return ram.percent >= self.ram_throttle_percent

    def is_gpu_ready(self, gpu: Optional[GpuTelemetry]) -> bool:
        return gpu is not None and gpu.cuda_available and gpu.free_vram_bytes > 0

    def evaluate_stress(self, snapshot: HardwareTelemetrySnapshot) -> str:
        cpu_hot = self.is_cpu_saturated(snapshot.cpu)
        ram_hot = self.is_memory_pressured(snapshot.ram)
        if cpu_hot and ram_hot:
            return "critical"
        if cpu_hot or ram_hot:
            return "elevated"
        return "normal"

    def evaluate_raw_load_level(self, snapshot: HardwareTelemetrySnapshot) -> tuple[LoadLevel, str]:
        cpu_load = snapshot.cpu.load_percent
        ram_pct = snapshot.ram.percent
        ram_avail_mb = snapshot.ram.available_bytes / (1024 * 1024)

        if cpu_load >= Settings.SYSTEM_CPU_EMERGENCY_PCT:
            return LoadLevel.EMERGENCY, f"cpu={cpu_load:.1f}%>={Settings.SYSTEM_CPU_EMERGENCY_PCT:.1f}%"
        if ram_pct >= Settings.SYSTEM_RAM_EMERGENCY_PCT:
            return LoadLevel.EMERGENCY, f"ram={ram_pct:.1f}%>={Settings.SYSTEM_RAM_EMERGENCY_PCT:.1f}%"
        if ram_avail_mb < Settings.SYSTEM_RAM_EMERGENCY_FREE_MB:
            return LoadLevel.EMERGENCY, f"ram_avail={int(ram_avail_mb)}MB<{Settings.SYSTEM_RAM_EMERGENCY_FREE_MB}MB"

        if cpu_load >= Settings.SYSTEM_CPU_CRITICAL_PCT:
            return LoadLevel.CRITICAL, f"cpu={cpu_load:.1f}%>={Settings.SYSTEM_CPU_CRITICAL_PCT:.1f}%"
        if ram_pct >= Settings.SYSTEM_RAM_CRITICAL_PCT:
            return LoadLevel.CRITICAL, f"ram={ram_pct:.1f}%>={Settings.SYSTEM_RAM_CRITICAL_PCT:.1f}%"
        if ram_avail_mb < Settings.SYSTEM_RAM_CRITICAL_FREE_MB:
            return LoadLevel.CRITICAL, f"ram_avail={int(ram_avail_mb)}MB<{Settings.SYSTEM_RAM_CRITICAL_FREE_MB}MB"

        if cpu_load >= Settings.SYSTEM_CPU_ELEVATED_PCT:
            return LoadLevel.ELEVATED, f"cpu={cpu_load:.1f}%>={Settings.SYSTEM_CPU_ELEVATED_PCT:.1f}%"
        if ram_pct >= Settings.SYSTEM_RAM_ELEVATED_PCT:
            return LoadLevel.ELEVATED, f"ram={ram_pct:.1f}%>={Settings.SYSTEM_RAM_ELEVATED_PCT:.1f}%"
        if ram_avail_mb < Settings.SYSTEM_RAM_ELEVATED_FREE_MB:
            return LoadLevel.ELEVATED, f"ram_avail={int(ram_avail_mb)}MB<{Settings.SYSTEM_RAM_ELEVATED_FREE_MB}MB"

        return LoadLevel.NORMAL, "healthy"

    @staticmethod
    def _tier_bounds(level: LoadLevel) -> tuple[float, float, int]:
        if level == LoadLevel.EMERGENCY:
            return (
                Settings.SYSTEM_CPU_EMERGENCY_PCT,
                Settings.SYSTEM_RAM_EMERGENCY_PCT,
                Settings.SYSTEM_RAM_EMERGENCY_FREE_MB,
            )
        if level == LoadLevel.CRITICAL:
            return (
                Settings.SYSTEM_CPU_CRITICAL_PCT,
                Settings.SYSTEM_RAM_CRITICAL_PCT,
                Settings.SYSTEM_RAM_CRITICAL_FREE_MB,
            )
        return (
            Settings.SYSTEM_CPU_ELEVATED_PCT,
            Settings.SYSTEM_RAM_ELEVATED_PCT,
            Settings.SYSTEM_RAM_ELEVATED_FREE_MB,
        )

    def _is_cool_to_drop_below(self, level: LoadLevel, snapshot: HardwareTelemetrySnapshot) -> bool:
        cpu_lim, ram_lim, free_floor = self._tier_bounds(level)
        band = Settings.SYSTEM_LOAD_HYSTERESIS_PCT
        ram_avail_mb = snapshot.ram.available_bytes / (1024 * 1024)
        return (
            snapshot.cpu.load_percent < (cpu_lim - band)
            and snapshot.ram.percent < (ram_lim - band)
            and ram_avail_mb >= (free_floor + 256)
        )

    def evaluate_load_level(self, snapshot: HardwareTelemetrySnapshot) -> tuple[LoadLevel, str]:
        raw_level, raw_reason = self.evaluate_raw_load_level(snapshot)
        with self._lock:
            if raw_level.severity_rank > self._current_level.severity_rank:
                self._current_level = raw_level
                self._cool_streak = 0
                self._last_reason = raw_reason
                return self._current_level, self._last_reason
            if raw_level == self._current_level:
                self._cool_streak = 0
                self._last_reason = raw_reason
                return self._current_level, self._last_reason
            if not self._is_cool_to_drop_below(self._current_level, snapshot):
                self._cool_streak = 0
                return self._current_level, self._last_reason
            self._cool_streak += 1
            required = Settings.SYSTEM_LOAD_RECOVERY_STREAK
            if self._cool_streak < required:
                return self._current_level, f"{self._last_reason} (cooling {self._cool_streak}/{required})"
            self._current_level = raw_level
            self._cool_streak = 0
            self._last_reason = raw_reason
            return self._current_level, self._last_reason

    def reset_hysteresis(self) -> None:
        with self._lock:
            self._current_level = LoadLevel.NORMAL
            self._cool_streak = 0
            self._last_reason = "healthy"

    def evaluate_gpu_health(
        self,
        snapshot: HardwareTelemetrySnapshot,
        breaker: Optional[HardwareCircuitBreaker] = None,
        encoder: str = "h264_nvenc",
    ) -> tuple[GpuHealthState, str]:
        if not Settings.SYSTEM_GPU_ENABLED:
            return GpuHealthState.DISABLED, "GPU disabled via SYSTEM_GPU_ENABLED=false"
        gpu = snapshot.gpu
        if gpu is None or not gpu.is_available:
            reason = gpu.unavailable_reason if (gpu is not None and gpu.unavailable_reason) else "No GPU detected"
            return GpuHealthState.UNAVAILABLE, reason
        if gpu.cuda_available and not gpu.nvenc_verified:
            return GpuHealthState.NVENC_FAILED, gpu.nvenc_failure_reason or "NVENC canary unverified"
        if breaker is not None and breaker.is_tripped(encoder):
            return GpuHealthState.CIRCUIT_OPEN, f"Encoder circuit {encoder} is OPEN"

        primary = gpu.devices[0] if gpu.devices else None
        temp_c = primary.temperature_c if primary is not None else 0
        gpu_util = primary.gpu_util_percent if primary is not None else 0.0

        if temp_c >= Settings.SYSTEM_GPU_MAX_TEMP_C:
            return GpuHealthState.THERMAL_THROTTLED, f"temp={temp_c}C>={Settings.SYSTEM_GPU_MAX_TEMP_C}C"
        if gpu_util >= Settings.SYSTEM_GPU_MAX_UTIL_PERCENT:
            return GpuHealthState.UTIL_SATURATED, f"gpu_util={gpu_util:.1f}%>={Settings.SYSTEM_GPU_MAX_UTIL_PERCENT:.1f}%"
        if gpu.total_vram_bytes > 0:
            total_vram_mb = max(1, gpu.total_vram_bytes // (1024 * 1024))
            free_vram_mb = gpu.free_vram_bytes // (1024 * 1024)
            used_vram_pct = ((total_vram_mb - free_vram_mb) / total_vram_mb) * 100.0
            if free_vram_mb < Settings.SYSTEM_GPU_MIN_FREE_VRAM_MB:
                return GpuHealthState.VRAM_PRESSURED, f"free_vram={free_vram_mb}MB<{Settings.SYSTEM_GPU_MIN_FREE_VRAM_MB}MB"
            if used_vram_pct >= Settings.SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT:
                return GpuHealthState.VRAM_PRESSURED, f"vram={used_vram_pct:.1f}%>={Settings.SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT:.1f}%"
        return GpuHealthState.HEALTHY, "healthy"
