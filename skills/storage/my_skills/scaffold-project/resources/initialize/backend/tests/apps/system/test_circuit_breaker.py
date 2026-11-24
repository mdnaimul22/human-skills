from __future__ import annotations
import concurrent.futures
import time
from src.apps.system.helpers import HardwareCircuitBreaker
from src.apps.system import CircuitState


def test_initial_state_closed_can_execute() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=3, cooldown_period=60.0)
    assert breaker.can_execute("h264_nvenc") is True
    assert breaker.get_state("h264_nvenc") == CircuitState.CLOSED
    assert breaker.is_tripped("h264_nvenc") is False


def test_consecutive_failures_trips_to_open() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=3, cooldown_period=60.0)
    breaker.record_failure("h264_nvenc", "Driver error")
    assert breaker.get_state("h264_nvenc") == CircuitState.CLOSED

    breaker.record_failure("h264_nvenc", "Timeout")
    assert breaker.get_state("h264_nvenc") == CircuitState.CLOSED

    breaker.record_failure("h264_nvenc", "Crashed")
    assert breaker.get_state("h264_nvenc") == CircuitState.OPEN
    assert breaker.is_tripped("h264_nvenc") is True
    assert breaker.can_execute("h264_nvenc") is False

    details = breaker.get_circuit_details("h264_nvenc")
    assert details.total_failures == 3
    assert details.consecutive_failures == 3
    assert details.last_error_reason == "Crashed"


def test_cooldown_expiration_transitions_to_half_open() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=2, cooldown_period=0.1)
    breaker.record_failure("hevc_vaapi", "Error 1")
    breaker.record_failure("hevc_vaapi", "Error 2")
    assert breaker.is_tripped("hevc_vaapi") is True

    time.sleep(0.12)
    assert breaker.get_state("hevc_vaapi") == CircuitState.HALF_OPEN
    assert breaker.can_execute("hevc_vaapi") is True
    assert breaker.can_execute("hevc_vaapi") is False


def test_half_open_failure_immediately_re_trips_to_open() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=2, cooldown_period=0.1)
    breaker.record_failure("h264_qsv", "Err")
    breaker.record_failure("h264_qsv", "Err")
    assert breaker.is_tripped("h264_qsv") is True

    time.sleep(0.12)
    assert breaker.can_execute("h264_qsv") is True

    breaker.record_failure("h264_qsv", "Trial failed")
    assert breaker.get_state("h264_qsv") == CircuitState.OPEN
    assert breaker.can_execute("h264_qsv") is False


def test_half_open_success_recovers_to_closed() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=2, cooldown_period=0.1)
    breaker.record_failure("libx264", "Err")
    breaker.record_failure("libx264", "Err")
    assert breaker.is_tripped("libx264") is True

    time.sleep(0.12)
    assert breaker.can_execute("libx264") is True

    breaker.record_success("libx264")
    assert breaker.get_state("libx264") == CircuitState.CLOSED
    assert breaker.can_execute("libx264") is True
    details = breaker.get_circuit_details("libx264")
    assert details.consecutive_failures == 0
    assert details.total_successes == 1


def test_half_open_lease_expiry_recovers_stuck_trial() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=1, cooldown_period=0.05, half_open_timeout=0.05)
    breaker.record_failure("nvenc", "Err")
    time.sleep(0.06)

    assert breaker.can_execute("nvenc") is True
    assert breaker.can_execute("nvenc") is False

    time.sleep(0.06)
    assert breaker.can_execute("nvenc") is True


def test_release_attempt_clears_in_flight() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=1, cooldown_period=0.05, half_open_timeout=10.0)
    breaker.record_failure("nvenc", "Err")
    time.sleep(0.06)

    assert breaker.can_execute("nvenc") is True
    assert breaker.can_execute("nvenc") is False

    breaker.release_attempt("nvenc")
    assert breaker.can_execute("nvenc") is True


def test_reset_encoder_and_all() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=1, cooldown_period=60.0)
    breaker.record_failure("enc1", "Err")
    breaker.record_failure("enc2", "Err")
    assert breaker.is_tripped("enc1") is True
    assert breaker.is_tripped("enc2") is True

    breaker.reset("enc1")
    assert breaker.is_tripped("enc1") is False
    assert breaker.is_tripped("enc2") is True

    breaker.reset()
    assert breaker.is_tripped("enc2") is False

    breaker.record_failure("enc1", "Err")
    breaker.record_failure("enc2", "Err")
    states = breaker.list_states()
    assert "enc1" in states and "enc2" in states
    breaker.reset_all()
    assert breaker.is_tripped("enc1") is False
    assert breaker.is_tripped("enc2") is False


def test_thread_concurrency_stress() -> None:
    breaker = HardwareCircuitBreaker(failure_threshold=5, cooldown_period=0.05)

    def worker(idx: int) -> None:
        enc = f"enc_{idx % 4}"
        for _ in range(50):
            if breaker.can_execute(enc):
                if idx % 3 == 0:
                    breaker.record_failure(enc, "simulated")
                else:
                    breaker.record_success(enc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(worker, i) for i in range(16)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

