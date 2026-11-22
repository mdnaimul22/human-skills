from __future__ import annotations
import threading
from typing import Optional
from src.config import Settings, setup_logger
from ..schema import LoadLevel, TokenType, WorkloadProfile, WorkloadType

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.allocator")


class ResourceAllocator:
    def __init__(
        self,
        max_encode_slots: Optional[int] = None,
        max_download_slots: Optional[int] = None,
        max_direct_slots: Optional[int] = None,
        profiles: Optional[dict[str, WorkloadProfile]] = None,
    ) -> None:
        self._lock = threading.Lock()
        self._profiles: dict[str, WorkloadProfile] = {}
        self._active_counts: dict[str, int] = {}
        self._explicit_encode_slots = max_encode_slots
        self._explicit_download_slots = max_download_slots
        self._explicit_direct_slots = max_direct_slots
        self._default_profile = WorkloadProfile(name="default", base_slots=1)
        self._seed_default_profiles()
        if profiles is not None:
            for p in profiles.values():
                self.register_profile(p)

    def _build_default_profiles(self) -> list[WorkloadProfile]:
        encode_slots = (
            self._explicit_encode_slots
            if self._explicit_encode_slots is not None
            else Settings.MAX_CONCURRENT_ENCODES
        )
        download_slots = (
            self._explicit_download_slots
            if self._explicit_download_slots is not None
            else Settings.MAX_CONCURRENT_DOWNLOADS
        )
        direct_slots = (
            self._explicit_direct_slots
            if self._explicit_direct_slots is not None
            else Settings.MAX_CONCURRENT_LIGHT_ENCODES
        )
        return [
            WorkloadProfile(
                name=WorkloadType.ENCODE.value,
                token_type=TokenType.HYBRID.value,
                base_slots=encode_slots,
                max_thread_cap=Settings.SYSTEM_ENCODE_MAX_THREADS,
                min_threads=1,
                min_ram_mb=256,
                max_ram_mb=2048,
                gpu_capable=True,
                vram_reserve_mb=Settings.SYSTEM_GPU_ENCODE_VRAM_MB,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.75,
                    LoadLevel.CRITICAL: 0.25,
                    LoadLevel.EMERGENCY: 0.25,
                },
            ),
            WorkloadProfile(
                name="video",
                token_type=TokenType.HYBRID.value,
                base_slots=encode_slots,
                max_thread_cap=Settings.SYSTEM_ENCODE_MAX_THREADS,
                min_threads=1,
                min_ram_mb=256,
                max_ram_mb=2048,
                gpu_capable=True,
                vram_reserve_mb=Settings.SYSTEM_GPU_ENCODE_VRAM_MB,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.75,
                    LoadLevel.CRITICAL: 0.25,
                    LoadLevel.EMERGENCY: 0.25,
                },
            ),
            WorkloadProfile(
                name=WorkloadType.DOWNLOAD.value,
                token_type=TokenType.NETWORK.value,
                base_slots=download_slots,
                max_thread_cap=4,
                min_threads=1,
                min_ram_mb=128,
                max_ram_mb=512,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.75,
                    LoadLevel.CRITICAL: 0.5,
                    LoadLevel.EMERGENCY: 0.25,
                },
            ),
            WorkloadProfile(
                name=WorkloadType.EGRESS.value,
                token_type=TokenType.NETWORK.value,
                base_slots=max(2, download_slots * 2),
                max_thread_cap=1,
                min_threads=1,
                min_ram_mb=64,
                max_ram_mb=128,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.75,
                    LoadLevel.CRITICAL: 0.5,
                    LoadLevel.EMERGENCY: 0.25,
                },
            ),
            WorkloadProfile(
                name=WorkloadType.DIRECT.value,
                token_type=TokenType.CPU.value,
                base_slots=direct_slots,
                max_thread_cap=4,
                min_threads=1,
                min_ram_mb=128,
                max_ram_mb=512,
            ),
            WorkloadProfile(
                name=WorkloadType.PROBE.value,
                token_type=TokenType.CPU.value,
                base_slots=max(2, Settings.MAX_CONCURRENT_ANALYSIS),
                max_thread_cap=2,
                min_threads=1,
                min_ram_mb=64,
                max_ram_mb=256,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.75,
                    LoadLevel.CRITICAL: 0.5,
                    LoadLevel.EMERGENCY: 0.25,
                },
            ),
            WorkloadProfile(
                name=WorkloadType.AUDIO.value,
                token_type=TokenType.CPU.value,
                base_slots=Settings.SYSTEM_MAX_AUDIO_SLOTS,
                max_thread_cap=2,
                min_threads=1,
                min_ram_mb=128,
                max_ram_mb=512,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.75,
                    LoadLevel.CRITICAL: 0.5,
                    LoadLevel.EMERGENCY: 0.25,
                },
            ),
            WorkloadProfile(
                name=WorkloadType.ML.value,
                token_type=TokenType.GPU.value,
                base_slots=Settings.SYSTEM_MAX_ML_SLOTS,
                max_thread_cap=4,
                min_threads=1,
                min_ram_mb=512,
                max_ram_mb=4096,
                gpu_capable=True,
                is_exclusive_gpu=True,
                vram_reserve_mb=Settings.SYSTEM_GPU_ML_VRAM_MB,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.5,
                    LoadLevel.CRITICAL: 0.0,
                    LoadLevel.EMERGENCY: 0.0,
                },
            ),
            WorkloadProfile(
                name=WorkloadType.RENDER.value,
                token_type=TokenType.HYBRID.value,
                base_slots=Settings.SYSTEM_MAX_RENDER_SLOTS,
                max_thread_cap=Settings.SYSTEM_RENDER_MAX_THREADS,
                min_threads=1,
                min_ram_mb=256,
                max_ram_mb=2048,
                gpu_capable=True,
                vram_reserve_mb=Settings.SYSTEM_GPU_ENCODE_VRAM_MB,
                degradation_matrix={
                    LoadLevel.NORMAL: 1.0,
                    LoadLevel.ELEVATED: 0.5,
                    LoadLevel.CRITICAL: 0.25,
                    LoadLevel.EMERGENCY: 0.0,
                },
            ),
        ]

    def _seed_default_profiles(self) -> None:
        for profile in self._build_default_profiles():
            self.register_profile(profile)

    def sync_from_settings(self) -> None:
        for profile in self._build_default_profiles():
            self.register_profile(profile)

    def register_profile(self, profile: WorkloadProfile) -> None:
        with self._lock:
            self._profiles[profile.name] = profile

    def has_profile(self, workload_type: str) -> bool:
        norm = workload_type.strip().lower()
        with self._lock:
            return norm in self._profiles

    def get_profile(self, workload_type: str) -> WorkloadProfile:
        norm = workload_type.strip().lower()
        with self._lock:
            return self._profiles.get(norm, self._default_profile)

    def get_capacity(self, workload_type: str, load_level: LoadLevel) -> int:
        profile = self.get_profile(workload_type)
        return profile.calculate_capacity(load_level)

    def can_admit(self, workload_type: str, load_level: LoadLevel) -> bool:
        norm = workload_type.strip().lower()
        capacity = self.get_capacity(norm, load_level)
        with self._lock:
            current = self._active_counts.get(norm, 0)
            return current < capacity

    def allocate(self, workload_type: str) -> None:
        norm = workload_type.strip().lower()
        with self._lock:
            self._active_counts[norm] = self._active_counts.get(norm, 0) + 1

    def release(self, workload_type: str) -> None:
        norm = workload_type.strip().lower()
        with self._lock:
            if norm in self._active_counts and self._active_counts[norm] > 0:
                self._active_counts[norm] -= 1

    def get_active(self, workload_type: str) -> int:
        norm = workload_type.strip().lower()
        with self._lock:
            return self._active_counts.get(norm, 0)

    def get_all_active(self) -> dict[str, int]:
        with self._lock:
            return dict(self._active_counts)

    def get_all_capacities(self, load_level: LoadLevel) -> dict[str, int]:
        with self._lock:
            return {name: profile.calculate_capacity(load_level) for name, profile in self._profiles.items()}
