import pytest
from src.apps.system import LoadLevel, TokenType, WorkloadProfile


def test_workload_profile_defaults() -> None:
    profile = WorkloadProfile(name="ML_INFERENCE")
    assert profile.name == "ml_inference"
    assert profile.token_type == TokenType.CPU.value
    assert profile.base_slots == 2
    assert profile.default_ttl == 300.0
    assert profile.calculate_capacity(LoadLevel.NORMAL) == 2
    assert profile.calculate_capacity(LoadLevel.ELEVATED) == 1
    assert profile.calculate_capacity(LoadLevel.CRITICAL) == 1
    assert profile.calculate_capacity(LoadLevel.EMERGENCY) == 0


def test_workload_profile_custom_capacity_matrix() -> None:
    profile = WorkloadProfile(
        name="browser_render",
        token_type=TokenType.RAM.value,
        base_slots=10,
        degradation_matrix={
            LoadLevel.NORMAL: 1.0,
            LoadLevel.ELEVATED: 0.5,
            LoadLevel.CRITICAL: 0.0,
            LoadLevel.EMERGENCY: 0.0,
        },
    )
    assert profile.calculate_capacity(LoadLevel.NORMAL) == 10
    assert profile.calculate_capacity(LoadLevel.ELEVATED) == 5
    assert profile.calculate_capacity(LoadLevel.CRITICAL) == 0
    assert profile.calculate_capacity(LoadLevel.EMERGENCY) == 0


def test_workload_profile_thread_calculation() -> None:
    profile = WorkloadProfile(name="encode_heavy", base_slots=4, max_thread_cap=8)
    assert profile.calculate_threads(16, LoadLevel.NORMAL) == 8
    assert profile.calculate_threads(16, LoadLevel.ELEVATED) == 8
    assert profile.calculate_threads(16, LoadLevel.CRITICAL) == 4
    assert profile.calculate_threads(16, LoadLevel.EMERGENCY) == 1


def test_workload_profile_validation_rejects_empty_name() -> None:
    with pytest.raises(Exception):
        WorkloadProfile(name="")

