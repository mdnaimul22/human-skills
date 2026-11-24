import concurrent.futures
from src.apps.system import LoadLevel, TokenType, WorkloadProfile
from src.apps.system.helpers import ResourceAllocator


def test_allocator_seeds_default_profiles() -> None:
    allocator = ResourceAllocator(max_encode_slots=2, max_download_slots=10, max_direct_slots=4)
    assert allocator.has_profile("encode")
    assert allocator.has_profile("download")
    assert allocator.has_profile("direct")
    assert allocator.has_profile("probe")
    assert allocator.has_profile("ml")
    assert allocator.has_profile("render")
    assert allocator.get_capacity("encode", LoadLevel.NORMAL) == 2
    assert allocator.get_capacity("download", LoadLevel.NORMAL) == 10


def test_allocator_dynamic_profile_registration() -> None:
    allocator = ResourceAllocator()
    custom_profile = WorkloadProfile(
        name="custom_transcribe",
        token_type=TokenType.HYBRID.value,
        base_slots=8,
        degradation_matrix={
            LoadLevel.NORMAL: 1.0,
            LoadLevel.ELEVATED: 0.5,
            LoadLevel.CRITICAL: 0.0,
            LoadLevel.EMERGENCY: 0.0,
        },
    )
    allocator.register_profile(custom_profile)
    assert allocator.has_profile("custom_transcribe")
    assert allocator.get_capacity("custom_transcribe", LoadLevel.NORMAL) == 8
    assert allocator.get_capacity("custom_transcribe", LoadLevel.ELEVATED) == 4
    assert allocator.get_capacity("custom_transcribe", LoadLevel.CRITICAL) == 0


def test_allocator_unknown_workload_fallback() -> None:
    allocator = ResourceAllocator()
    assert allocator.has_profile("unregistered_task") is False
    assert allocator.get_capacity("unregistered_task", LoadLevel.NORMAL) == 1
    assert allocator.get_capacity("unregistered_task", LoadLevel.EMERGENCY) == 0


def test_allocator_admission_and_release_lifecycle() -> None:
    allocator = ResourceAllocator(max_encode_slots=1)
    assert allocator.can_admit("encode", LoadLevel.NORMAL) is True
    allocator.allocate("encode")
    assert allocator.get_active("encode") == 1
    assert allocator.can_admit("encode", LoadLevel.NORMAL) is False

    allocator.release("encode")
    assert allocator.get_active("encode") == 0
    assert allocator.can_admit("encode", LoadLevel.NORMAL) is True

    allocator.release("encode")
    assert allocator.get_active("encode") == 0


def test_allocator_thread_safe_concurrent_allocations() -> None:
    allocator = ResourceAllocator(max_download_slots=100)

    def worker() -> None:
        for _ in range(50):
            allocator.allocate("download")
            allocator.release("download")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker) for _ in range(8)]
        for f in futures:
            f.result()

    assert allocator.get_active("download") == 0


def test_allocator_get_all_capacities() -> None:
    allocator = ResourceAllocator(max_encode_slots=2, max_download_slots=4)
    caps = allocator.get_all_capacities(LoadLevel.NORMAL)
    assert "encode" in caps
    assert "download" in caps
    assert caps["encode"] == 2
    assert caps["download"] == 4
