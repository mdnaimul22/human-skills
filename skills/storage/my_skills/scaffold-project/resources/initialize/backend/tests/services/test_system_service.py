from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.apps.system import GpuHealthState
from src.schema.system import SubsystemStatus
from src.services.apps.system import SystemService


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (GpuHealthState.HEALTHY, SubsystemStatus.HEALTHY),
        (GpuHealthState.VRAM_PRESSURED, SubsystemStatus.DEGRADED),
        (GpuHealthState.THERMAL_THROTTLED, SubsystemStatus.DEGRADED),
        (GpuHealthState.UTIL_SATURATED, SubsystemStatus.DEGRADED),
        (GpuHealthState.CIRCUIT_OPEN, SubsystemStatus.DEGRADED),
        (GpuHealthState.NVENC_FAILED, SubsystemStatus.DEGRADED),
        (GpuHealthState.UNAVAILABLE, SubsystemStatus.UNHEALTHY),
        (GpuHealthState.DISABLED, SubsystemStatus.UNHEALTHY),
    ],
)
def test_system_service_check_gpu_maps_all_health_states(
    state: GpuHealthState,
    expected: SubsystemStatus,
) -> None:
    mock_sm = MagicMock()
    mock_sm.get_gpu_health.return_value = (state, f"reason:{state.value}")
    with patch("src.services.apps.system.get_system_manager", return_value=mock_sm):
        report = SystemService()._check_gpu()
    assert report.status == expected
