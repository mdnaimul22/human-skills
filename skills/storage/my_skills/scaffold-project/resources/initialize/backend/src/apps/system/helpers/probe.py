from __future__ import annotations
import asyncio
import concurrent.futures
import hashlib
import os
import threading
import time
from typing import Optional
import weakref
import psutil
from src.config import Settings, setup_logger, sys_exists, sys_read_text
from ..schema import (
    CpuTelemetry,
    GpuTelemetry,
    HardwareTelemetrySnapshot,
    RamTelemetry,
)
from .circuit_breaker import HardwareCircuitBreaker, get_circuit_breaker
from .gpu_detector import GpuDetector

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.probe")


class HardwareProbe:
    _instance: Optional[HardwareProbe] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        circuit_breaker: Optional[HardwareCircuitBreaker] = None,
        cache_ttl: Optional[float] = None,
        canary_timeout: Optional[float] = None,
        gpu_detector: Optional[GpuDetector] = None,
    ) -> None:
        self.circuit_breaker = circuit_breaker or get_circuit_breaker()
        self.gpu_detector = gpu_detector or GpuDetector()
        self._explicit_cache_ttl = cache_ttl
        self.canary_timeout = canary_timeout if canary_timeout is not None else Settings.SYSTEM_GPU_CANARY_TIMEOUT_SEC
        self._cached_snapshot: Optional[HardwareTelemetrySnapshot] = None
        self._cached_at: float = 0.0
        self._cpu_ewma: Optional[float] = None
        self._thread_lock = threading.Lock()
        self._loop_locks: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = weakref.WeakKeyDictionary()
        self._fallback_loop_lock: Optional[asyncio.Lock] = None
        try:
            psutil.cpu_percent(interval=None)
        except Exception as e:
            logger.warning(f"CPU percent initial warmup encountered warning: {e}")

    @property
    def cache_ttl(self) -> float:
        if self._explicit_cache_ttl is not None:
            return self._explicit_cache_ttl
        return Settings.SYSTEM_TELEMETRY_CACHE_TTL_SEC

    def _get_loop_lock(self) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
            with self._thread_lock:
                lock = self._loop_locks.get(loop)
                if lock is None:
                    lock = asyncio.Lock()
                    self._loop_locks[loop] = lock
                return lock
        except RuntimeError:
            with self._thread_lock:
                if self._fallback_loop_lock is None:
                    self._fallback_loop_lock = asyncio.Lock()
                return self._fallback_loop_lock

    @classmethod
    def get_instance(cls, cache_ttl: Optional[float] = None, canary_timeout: Optional[float] = None) -> HardwareProbe:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls(cache_ttl=cache_ttl, canary_timeout=canary_timeout)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            if cls._instance is not None:
                cls._instance.shutdown()
            cls._instance = None

    def _sample_cpu_sync(self, warmup: bool = False) -> CpuTelemetry:
        logical = os.cpu_count() or 1
        try:
            physical = psutil.cpu_count(logical=False) or 1
        except Exception as exc:
            logger.debug(f"psutil physical core count fallback: {exc}")
            physical = 1
        physical = max(1, min(physical, logical))
        try:
            raw_pct = float(psutil.cpu_percent(interval=0.15 if warmup else None))
        except Exception as exc:
            logger.debug(f"psutil cpu_percent fallback: {exc}")
            raw_pct = 0.0
        raw_pct = max(0.0, min(100.0, raw_pct))
        alpha = Settings.SYSTEM_CPU_EWMA_ALPHA
        with self._thread_lock:
            if self._cpu_ewma is None:
                smoothed = raw_pct
            else:
                smoothed = (alpha * raw_pct) + ((1.0 - alpha) * self._cpu_ewma)
            self._cpu_ewma = max(0.0, min(100.0, round(smoothed, 2)))
            load_ewma = self._cpu_ewma
        try:
            load_1, load_5, load_15 = os.getloadavg()
        except (AttributeError, OSError):
            load_1, load_5, load_15 = (raw_pct / 100.0) * logical, 0.0, 0.0
        cgroup_quota: Optional[float] = None
        if sys_exists("/sys/fs/cgroup/cpu.max"):
            try:
                parts = sys_read_text("/sys/fs/cgroup/cpu.max").strip().split()
                if len(parts) >= 2 and parts[0] != "max":
                    cgroup_quota = float(parts[0]) / float(parts[1])
            except Exception as e:
                logger.debug(f"cgroups v2 cpu.max inspection skipped: {e}")
        effective = logical
        if cgroup_quota is not None and cgroup_quota > 0.0:
            effective = max(1, min(logical, int(cgroup_quota)))
        return CpuTelemetry(
            logical_cores=logical,
            physical_cores=physical,
            effective_cores=effective,
            load_percent=load_ewma,
            raw_load_percent=raw_pct,
            load_1m=max(0.0, float(load_1)),
            load_5m=max(0.0, float(load_5)),
            load_15m=max(0.0, float(load_15)),
            cgroup_quota_cores=cgroup_quota,
        )

    def _read_cgroup_current_used(self) -> int:
        if not sys_exists("/sys/fs/cgroup/memory.current"):
            return 0
        try:
            return int(sys_read_text("/sys/fs/cgroup/memory.current").strip())
        except Exception as err:
            logger.debug(f"cgroups memory.current read skipped: {err}")
            return 0

    def _read_cgroup_memory_limit(self, total: int, available: int, used: int) -> tuple[int, int, int]:
        if not sys_exists("/sys/fs/cgroup/memory.max"):
            return total, available, used
        try:
            val = sys_read_text("/sys/fs/cgroup/memory.max").strip()
            if val == "max":
                return total, available, used
            cgroup_bytes = int(val)
            if cgroup_bytes >= total:
                return total, available, used
            total = cgroup_bytes
            current_used = self._read_cgroup_current_used()
            available = min(available, max(0, total - current_used))
            used = min(total, current_used if current_used > 0 else used)
        except Exception as e:
            logger.debug(f"cgroups memory limit evaluation skipped: {e}")
        return total, available, used

    def _sample_process_rss_bytes(self) -> int:
        try:
            proc = psutil.Process(os.getpid())
            total_rss = int(proc.memory_info().rss)
            for child in proc.children(recursive=True):
                try:
                    total_rss += int(child.memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as err:
                    logger.debug(f"Child RSS read skipped: {err}")
            return max(0, total_rss)
        except Exception as exc:
            logger.warning(f"Failed reading process-tree RSS: {exc}")
            return 0

    def _sample_ram_sync(self) -> RamTelemetry:
        try:
            vm = psutil.virtual_memory()
            sm = psutil.swap_memory()
            total = int(vm.total)
            available = int(vm.available)
            used = int(vm.used)
            free = int(vm.free)
            swap_total = int(sm.total)
            swap_used = int(sm.used)
        except Exception as exc:
            logger.warning(f"psutil memory query failed, reading /proc/meminfo: {exc}")
            total, available, free, swap_total, swap_used = self._read_procfs_meminfo()
            used = total - available
        total, available, used = self._read_cgroup_memory_limit(total, available, used)
        free = max(0, total - used)
        calc_percent = round(((total - available) / total) * 100.0, 1) if total > 0 else 0.0
        process_rss = self._sample_process_rss_bytes()
        return RamTelemetry(
            total_bytes=total,
            available_bytes=available,
            used_bytes=used,
            free_bytes=free,
            percent=max(0.0, min(100.0, calc_percent)),
            swap_total_bytes=swap_total,
            swap_used_bytes=swap_used,
            process_rss_bytes=process_rss,
        )

    def _read_procfs_meminfo(self) -> tuple[int, int, int, int, int]:
        if not sys_exists("/proc/meminfo"):
            return 1024**3, 512 * (1024**2), 512 * (1024**2), 0, 0
        try:
            content = sys_read_text("/proc/meminfo")
            values: dict[str, int] = {}
            for line in content.splitlines():
                parts = line.split(":")
                if len(parts) >= 2:
                    key = parts[0].strip()
                    val = int(parts[1].strip().split()[0]) * 1024
                    values[key] = val
            mem_total = values.get("MemTotal", 1024**3)
            mem_avail = values.get("MemAvailable", values.get("MemFree", 512 * (1024**2)))
            mem_free = values.get("MemFree", 512 * (1024**2))
            swap_total = values.get("SwapTotal", 0)
            swap_free = values.get("SwapFree", 0)
            return mem_total, mem_avail, mem_free, swap_total, swap_total - swap_free
        except Exception as e:
            logger.error(f"Failed to read /proc/meminfo: {e}")
            return 1024**3, 512 * (1024**2), 512 * (1024**2), 0, 0

    def _sample_gpu_sync(self, force_capability_recheck: bool = False) -> Optional[GpuTelemetry]:
        return self.gpu_detector.sample(
            include_nvenc_check=True,
            force_capability_recheck=force_capability_recheck,
        )

    @staticmethod
    def _compute_fingerprint(cpu: CpuTelemetry, ram: RamTelemetry, gpu: Optional[GpuTelemetry]) -> str:
        gpu_part = (
            f"{gpu.name}:{gpu.total_vram_bytes}:{gpu.driver_version}:{gpu.backend.value}"
            if gpu is not None
            else "none"
        )
        raw = f"{cpu.physical_cores}:{cpu.logical_cores}:{cpu.effective_cores}:{ram.total_bytes}:{gpu_part}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    async def sample(
        self,
        force_refresh: bool = False,
        warmup: bool = False,
        force_capability_recheck: bool = False,
    ) -> HardwareTelemetrySnapshot:
        bypass_cache = force_refresh or warmup or force_capability_recheck
        now = time.time()
        with self._thread_lock:
            if not bypass_cache and self._cached_snapshot and (now - self._cached_at) < self.cache_ttl:
                return self._cached_snapshot
        lock = self._get_loop_lock()
        async with lock:
            now = time.time()
            with self._thread_lock:
                if not bypass_cache and self._cached_snapshot and (now - self._cached_at) < self.cache_ttl:
                    return self._cached_snapshot
            cpu_telemetry, ram_telemetry, gpu_telemetry = await asyncio.gather(
                asyncio.to_thread(self._sample_cpu_sync, warmup),
                asyncio.to_thread(self._sample_ram_sync),
                asyncio.to_thread(self._sample_gpu_sync, force_capability_recheck),
            )
            snapshot = HardwareTelemetrySnapshot(
                timestamp=now,
                cpu=cpu_telemetry,
                ram=ram_telemetry,
                gpu=gpu_telemetry,
                fingerprint=self._compute_fingerprint(cpu_telemetry, ram_telemetry, gpu_telemetry),
            )
            with self._thread_lock:
                self._cached_snapshot = snapshot
                self._cached_at = now
            return snapshot

    def run(
        self,
        force_refresh: bool = False,
        warmup: bool = False,
        force_capability_recheck: bool = False,
    ) -> HardwareTelemetrySnapshot:
        bypass_cache = force_refresh or warmup or force_capability_recheck
        now = time.time()
        with self._thread_lock:
            if not bypass_cache and self._cached_snapshot and (now - self._cached_at) < self.cache_ttl:
                return self._cached_snapshot
        coro = self.sample(
            force_refresh=force_refresh,
            warmup=warmup,
            force_capability_recheck=force_capability_recheck,
        )
        try:
            if asyncio.get_running_loop().is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    return ex.submit(asyncio.run, coro).result()
        except RuntimeError as e:
            logger.debug(f"Event loop check: {e}")
        return asyncio.run(coro)

    def shutdown(self) -> None:
        self.gpu_detector.shutdown()


def get_hardware_probe(cache_ttl: Optional[float] = None, canary_timeout: Optional[float] = None) -> HardwareProbe:
    return HardwareProbe.get_instance(cache_ttl=cache_ttl, canary_timeout=canary_timeout)


def get_current_hardware_snapshot(force_refresh: bool = False) -> HardwareTelemetrySnapshot:
    probe = get_hardware_probe()
    return probe.run(force_refresh=force_refresh)
