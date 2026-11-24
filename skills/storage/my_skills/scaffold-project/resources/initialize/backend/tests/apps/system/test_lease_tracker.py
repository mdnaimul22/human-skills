from __future__ import annotations
import concurrent.futures
import time
from src.apps.system import TokenType
from src.apps.system.helpers import LeaseTracker


def test_lease_tracker_ledger_accounting_and_idempotent_release() -> None:
    tracker = LeaseTracker(default_ttl=60.0)
    l1 = tracker.create_lease(
        "encode",
        "j1",
        token_type=TokenType.HYBRID.value,
        cpu_cores_allocated=2,
        memory_bytes_allocated=1024 * 1024 * 1024,
        gpu_device_id=0,
        vram_bytes_allocated=512 * 1024 * 1024,
    )
    l2 = tracker.create_lease(
        "download",
        "j2",
        token_type=TokenType.NETWORK.value,
        cpu_cores_allocated=1,
        memory_bytes_allocated=256 * 1024 * 1024,
    )

    snap = tracker.get_commitment_snapshot()
    assert snap.active_leases == 2
    assert snap.committed_threads == 3
    assert snap.committed_ram_mb == 1280
    assert snap.committed_gpu_sessions == 1
    assert snap.committed_vram_mb == 512
    assert snap.active_by_workload == {"encode": 1, "download": 1}
    assert tracker.get_unmaterialized_vram_mb(window_sec=5.0) == 512

    assert tracker.release_lease(l1) is True
    assert tracker.release_lease(l1) is False
    snap_after = tracker.get_commitment_snapshot()
    assert snap_after.active_leases == 1
    assert snap_after.committed_threads == 1
    assert snap_after.committed_ram_mb == 256
    assert snap_after.committed_gpu_sessions == 0
    assert snap_after.committed_vram_mb == 0

    assert tracker.release_lease(l2) is True
    assert tracker.get_commitment_snapshot().active_leases == 0


def test_lease_tracker_reap_expired_reclaims_ledger_and_prevents_double_decrement() -> None:
    tracker = LeaseTracker(default_ttl=0.02)
    lease = tracker.create_lease(
        "render",
        "j_exp",
        ttl=0.01,
        token_type=TokenType.HYBRID.value,
        cpu_cores_allocated=4,
        memory_bytes_allocated=512 * 1024 * 1024,
        gpu_device_id=0,
        vram_bytes_allocated=512 * 1024 * 1024,
    )
    time.sleep(0.02)
    expired = tracker.reap_expired()
    assert len(expired) == 1
    assert tracker.release_lease(lease) is False

    snap = tracker.get_commitment_snapshot()
    assert snap.active_leases == 0
    assert snap.committed_threads == 0
    assert snap.committed_ram_mb == 0
    assert snap.committed_gpu_sessions == 0
    assert snap.committed_vram_mb == 0


def test_lease_tracker_thread_concurrency_stress() -> None:
    tracker = LeaseTracker(default_ttl=60.0)

    def worker(idx: int) -> None:
        for step in range(25):
            lease = tracker.create_lease(
                "encode",
                f"job_{idx}_{step}",
                token_type=TokenType.HYBRID.value,
                cpu_cores_allocated=2,
                memory_bytes_allocated=256 * 1024 * 1024,
                gpu_device_id=0,
                vram_bytes_allocated=512 * 1024 * 1024,
            )
            tracker.release_lease(lease)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(worker, i) for i in range(8)]
        for f in futures:
            f.result()

    snap = tracker.get_commitment_snapshot()
    assert snap.active_leases == 0
    assert snap.committed_threads == 0
    assert snap.committed_ram_mb == 0
    assert snap.committed_gpu_sessions == 0
    assert snap.committed_vram_mb == 0
