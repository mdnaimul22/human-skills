from __future__ import annotations
import asyncio
import os
import shutil
import time
from src.apps.jobs import get_job_manager
from src.apps.system import GpuHealthState, SystemStatusSnapshot, get_system_manager
from src.config import Settings, setup_logger
from src.db import get_db_manager
from src.helpers import get_now_iso
from src.schema.system import (
    LivenessResponse,
    LivenessStatus,
    ReadinessChecks,
    ReadinessResponse,
    ReadinessStatus,
    RootMetadataResponse,
    ServiceStatus,
    StorageHealthReport,
    SubsystemHealthReport,
    SubsystemStatus,
)

logger = setup_logger(Settings.LOG_DIR / "service.log", name="services.apps.system")
_DEGRADED_GPU_STATES: frozenset[GpuHealthState] = frozenset({
    GpuHealthState.VRAM_PRESSURED,
    GpuHealthState.THERMAL_THROTTLED,
    GpuHealthState.UTIL_SATURATED,
    GpuHealthState.CIRCUIT_OPEN,
    GpuHealthState.NVENC_FAILED,
})
_START_TIME = time.time()

class SystemService:
    def __init__(self) -> None:
        self._cached_readiness: ReadinessResponse | None = None
        self._cache_lock = asyncio.Lock()
        self._last_evaluated_at: float = 0.0
        self._is_shutting_down: bool = False

    def mark_shutting_down(self) -> None:
        self._is_shutting_down = True

    def get_root_metadata(self) -> RootMetadataResponse:
        uptime = max(0.0, time.time() - _START_TIME)
        status = ServiceStatus.DEGRADED if self._is_shutting_down else ServiceStatus.ONLINE
        docs_url = "/docs" if not Settings.is_production else None
        return RootMetadataResponse(
            name=Settings.PROJECT_NAME,
            version=Settings.VERSION,
            environment=Settings.ENV,
            status=status,
            message=f"{Settings.PROJECT_NAME} Core Engine operational",
            server_time=get_now_iso(),
            uptime_seconds=round(uptime, 2),
            docs_url=docs_url,
        )

    def get_liveness(self) -> LivenessResponse:
        status = LivenessStatus.SHUTTING_DOWN if self._is_shutting_down else LivenessStatus.OK
        active_jobs = get_job_manager().active_count()
        return LivenessResponse(
            status=status,
            timestamp=time.time(),
            pid=os.getpid(),
            active_jobs=active_jobs,
            version=Settings.VERSION,
        )

    async def _check_database(self) -> SubsystemHealthReport:
        t0 = time.perf_counter()
        try:
            is_ok = await asyncio.wait_for(get_db_manager().ping(), timeout=1.0)
            latency = (time.perf_counter() - t0) * 1000.0
            if is_ok:
                return SubsystemHealthReport(
                    status=SubsystemStatus.HEALTHY,
                    latency_ms=round(latency, 2),
                    message="Database reachable and responsive",
                )
            return SubsystemHealthReport(
                status=SubsystemStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message="Database ping query failed",
            )
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            return SubsystemHealthReport(
                status=SubsystemStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=f"Database connection error: {e}",
            )

    def _check_storage(self) -> StorageHealthReport:
        try:
            stat = shutil.disk_usage(Settings.TEMP_DIR)
            free_mb = stat.free // (1024 * 1024)
            total_mb = stat.total // (1024 * 1024)
            used_pct = round(((stat.total - stat.free) / stat.total) * 100.0, 1)
            min_free_mb = Settings.MAX_FILE_SIZE_MB * 2
            if free_mb < min_free_mb:
                return StorageHealthReport(
                    status=SubsystemStatus.UNHEALTHY,
                    free_mb=free_mb,
                    total_mb=total_mb,
                    used_percent=used_pct,
                    message=f"Low disk space: {free_mb}MB free (minimum required: {min_free_mb}MB)",
                )
            return StorageHealthReport(
                status=SubsystemStatus.HEALTHY,
                free_mb=free_mb,
                total_mb=total_mb,
                used_percent=used_pct,
                message="Sufficient disk storage available",
            )
        except Exception as e:
            return StorageHealthReport(
                status=SubsystemStatus.UNHEALTHY,
                free_mb=0,
                total_mb=0,
                used_percent=100.0,
                message=f"Storage probe failed: {e}",
            )

    def _check_gpu(self) -> SubsystemHealthReport:
        try:
            sm = get_system_manager()
            gpu_health, reason = sm.get_gpu_health()
            if gpu_health == GpuHealthState.HEALTHY:
                return SubsystemHealthReport(
                    status=SubsystemStatus.HEALTHY,
                    latency_ms=0.0,
                    message="GPU telemetry optimal",
                )
            if gpu_health in _DEGRADED_GPU_STATES:
                return SubsystemHealthReport(
                    status=SubsystemStatus.DEGRADED,
                    latency_ms=0.0,
                    message=f"GPU degraded (CPU fallback enabled): {reason}",
                )
            return SubsystemHealthReport(
                status=SubsystemStatus.UNHEALTHY,
                latency_ms=0.0,
                message=f"GPU offline or throttled: {reason}",
            )
        except Exception as e:
            return SubsystemHealthReport(
                status=SubsystemStatus.DEGRADED,
                latency_ms=0.0,
                message=f"GPU evaluation bypassed: {e}",
            )

    def _check_egress(self) -> SubsystemHealthReport:
        return SubsystemHealthReport(
            status=SubsystemStatus.HEALTHY,
            latency_ms=0.0,
            message="Direct network routing active",
        )

    def _check_jobs(self) -> SubsystemHealthReport:
        try:
            active = get_job_manager().active_count()
            limit = Settings.MAX_CONCURRENT_JOBS
            if active >= limit:
                return SubsystemHealthReport(
                    status=SubsystemStatus.DEGRADED,
                    latency_ms=0.0,
                    message=f"Job capacity saturated ({active}/{limit})",
                )
            return SubsystemHealthReport(
                status=SubsystemStatus.HEALTHY,
                latency_ms=0.0,
                message=f"Job manager accepting workloads ({active}/{limit})",
            )
        except Exception as e:
            return SubsystemHealthReport(
                status=SubsystemStatus.UNHEALTHY,
                latency_ms=0.0,
                message=f"Job manager probe error: {e}",
            )

    async def evaluate_readiness(self, force_refresh: bool = False) -> ReadinessResponse:
        now = time.time()
        if not force_refresh and self._cached_readiness is not None and (now - self._last_evaluated_at < 5.0):
            return self._cached_readiness

        async with self._cache_lock:
            if not force_refresh and self._cached_readiness is not None and (now - self._last_evaluated_at < 5.0):
                return self._cached_readiness

            db_report = await self._check_database()
            storage_report = self._check_storage()
            gpu_report = self._check_gpu()
            egress_report = self._check_egress()
            jobs_report = self._check_jobs()

            degraded_reasons: list[str] = []
            is_unready = self._is_shutting_down or (db_report.status == SubsystemStatus.UNHEALTHY) or (storage_report.status == SubsystemStatus.UNHEALTHY)

            for name, rep in (
                ("database", db_report),
                ("storage", storage_report),
                ("gpu", gpu_report),
                ("egress", egress_report),
                ("jobs", jobs_report),
            ):
                if rep.status != SubsystemStatus.HEALTHY:
                    degraded_reasons.append(f"{name}: {rep.message}")

            if is_unready:
                status = ReadinessStatus.UNREADY
            elif degraded_reasons:
                status = ReadinessStatus.DEGRADED
            else:
                status = ReadinessStatus.READY

            checks = ReadinessChecks(
                database=db_report,
                storage=storage_report,
                gpu_governor=gpu_report,
                network_egress=egress_report,
                jobs=jobs_report,
            )
            response = ReadinessResponse(
                status=status,
                timestamp=now,
                version=Settings.VERSION,
                checks=checks,
                degraded_reasons=degraded_reasons,
            )
            self._cached_readiness = response
            self._last_evaluated_at = now
            return response

    async def get_system_status(self, force_refresh: bool = False) -> SystemStatusSnapshot:
        return await get_system_manager().get_status_snapshot_async(force_refresh=force_refresh)

_system_service = SystemService()

def get_system_service() -> SystemService:
    return _system_service
