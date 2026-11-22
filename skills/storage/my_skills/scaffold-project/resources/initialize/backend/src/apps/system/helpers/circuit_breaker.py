from __future__ import annotations
import threading
import time
from typing import Optional
from src.config import Settings, setup_logger
from ..schema import CircuitState, EncoderCircuitState

logger = setup_logger(Settings.LOG_DIR / "system.log", name="apps.system.circuit_breaker")


class HardwareCircuitBreaker:
    _instance: Optional[HardwareCircuitBreaker] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(
        self, failure_threshold: Optional[int] = None, cooldown_period: Optional[float] = None,
        cooldown_seconds: Optional[float] = None, cooldown_window_seconds: Optional[float] = None,
        half_open_timeout: Optional[float] = None,
    ) -> None:
        eff_threshold = failure_threshold if failure_threshold is not None else Settings.SYSTEM_BREAKER_FAILURE_THRESHOLD
        effective_cooldown = cooldown_period if cooldown_period is not None else Settings.SYSTEM_BREAKER_COOLDOWN_SEC
        if cooldown_seconds is not None:
            effective_cooldown = cooldown_seconds
        elif cooldown_window_seconds is not None:
            effective_cooldown = cooldown_window_seconds
        eff_half_open = half_open_timeout if half_open_timeout is not None else Settings.SYSTEM_BREAKER_HALF_OPEN_TIMEOUT_SEC
        self.failure_threshold = eff_threshold
        self.cooldown_period = effective_cooldown
        self.half_open_timeout = eff_half_open
        self._states: dict[str, EncoderCircuitState] = {}
        self._lock = threading.Lock()

    @property
    def cooldown_seconds(self) -> float:
        return self.cooldown_period

    @cooldown_seconds.setter
    def cooldown_seconds(self, value: float) -> None:
        self.cooldown_period = value

    @property
    def cooldown_window_seconds(self) -> float:
        return self.cooldown_period

    @cooldown_window_seconds.setter
    def cooldown_window_seconds(self, value: float) -> None:
        self.cooldown_period = value

    @classmethod
    def get_instance(
        cls, failure_threshold: Optional[int] = None, cooldown_period: Optional[float] = None,
        cooldown_seconds: Optional[float] = None, cooldown_window_seconds: Optional[float] = None,
    ) -> HardwareCircuitBreaker:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls(
                        failure_threshold=failure_threshold, cooldown_period=cooldown_period,
                        cooldown_seconds=cooldown_seconds, cooldown_window_seconds=cooldown_window_seconds,
                    )
        return cls._instance

    def _get_or_create(self, encoder: str) -> EncoderCircuitState:
        if encoder not in self._states:
            self._states[encoder] = EncoderCircuitState(encoder_name=encoder)
        return self._states[encoder]

    def can_attempt(self, encoder: str) -> bool:
        return self.can_execute(encoder)

    def is_tripped(self, encoder: str) -> bool:
        return self.get_state(encoder) == CircuitState.OPEN

    def release_attempt(self, encoder: str) -> None:
        with self._lock:
            if encoder in self._states:
                self._states[encoder].half_open_in_flight = False
                self._states[encoder].half_open_lease_expiry = 0.0

    def can_execute(self, encoder: str) -> bool:
        with self._lock:
            state_rec = self._get_or_create(encoder)
            now = time.time()
            if state_rec.state == CircuitState.CLOSED:
                return True
            if state_rec.state == CircuitState.OPEN:
                if now >= state_rec.cooldown_until:
                    state_rec.state = CircuitState.HALF_OPEN
                    state_rec.half_open_in_flight = True
                    state_rec.half_open_lease_expiry = now + self.half_open_timeout
                    logger.info(f"Circuit breaker for {encoder} entered HALF_OPEN state")
                    return True
                return False
            if state_rec.state == CircuitState.HALF_OPEN:
                lease_expired = state_rec.half_open_in_flight and (now >= state_rec.half_open_lease_expiry)
                if not state_rec.half_open_in_flight or lease_expired:
                    state_rec.half_open_in_flight = True
                    state_rec.half_open_lease_expiry = now + self.half_open_timeout
                    return True
                return False
            return True

    def record_success(self, encoder: str) -> None:
        with self._lock:
            state_rec = self._get_or_create(encoder)
            now = time.time()
            state_rec.total_successes += 1
            state_rec.last_success_time = now
            state_rec.consecutive_failures = 0
            state_rec.half_open_in_flight = False
            state_rec.half_open_lease_expiry = 0.0
            if state_rec.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                logger.info(f"Hardware encoder {encoder} recovered, reset to CLOSED")
            state_rec.state = CircuitState.CLOSED

    def record_failure(self, encoder: str, reason: str = "") -> None:
        with self._lock:
            state_rec = self._get_or_create(encoder)
            now = time.time()
            state_rec.consecutive_failures += 1
            state_rec.total_failures += 1
            state_rec.last_failure_time = now
            state_rec.last_error_reason = reason[:200]
            state_rec.half_open_in_flight = False
            state_rec.half_open_lease_expiry = 0.0
            if state_rec.state == CircuitState.HALF_OPEN:
                state_rec.state = CircuitState.OPEN
                state_rec.cooldown_until = now + self.cooldown_period
                logger.error(f"Half-open trial probe failed for {encoder}: {reason}")
                return
            if state_rec.consecutive_failures >= self.failure_threshold:
                state_rec.state = CircuitState.OPEN
                state_rec.cooldown_until = now + self.cooldown_period
                logger.error(f"Encoder {encoder} reached failure threshold, TRIPPED to OPEN: {reason}")

    def get_state(self, encoder: str) -> CircuitState:
        with self._lock:
            state_rec = self._get_or_create(encoder)
            now = time.time()
            if state_rec.state == CircuitState.OPEN and now >= state_rec.cooldown_until:
                state_rec.state = CircuitState.HALF_OPEN
                state_rec.half_open_in_flight = False
                state_rec.half_open_lease_expiry = 0.0
            return state_rec.state

    def get_circuit_details(self, encoder: str) -> EncoderCircuitState:
        with self._lock:
            state_rec = self._get_or_create(encoder)
            now = time.time()
            if state_rec.state == CircuitState.OPEN and now >= state_rec.cooldown_until:
                state_rec.state = CircuitState.HALF_OPEN
                state_rec.half_open_in_flight = False
                state_rec.half_open_lease_expiry = 0.0
            return state_rec.model_copy()

    def reset(self, encoder: Optional[str] = None) -> None:
        with self._lock:
            if encoder:
                if encoder in self._states:
                    self._states[encoder] = EncoderCircuitState(encoder_name=encoder)
                    logger.info(f"Encoder circuit breaker reset for {encoder}")
            else:
                self._states.clear()
                logger.info("All hardware encoder circuit breakers cleared")

    def reset_all(self) -> None:
        self.reset(None)

    def list_states(self) -> dict[str, EncoderCircuitState]:
        with self._lock:
            now = time.time()
            result: dict[str, EncoderCircuitState] = {}
            for name, state_rec in self._states.items():
                if state_rec.state == CircuitState.OPEN and now >= state_rec.cooldown_until:
                    state_rec.state = CircuitState.HALF_OPEN
                    state_rec.half_open_in_flight = False
                    state_rec.half_open_lease_expiry = 0.0
                result[name] = state_rec.model_copy()
            return result


def get_circuit_breaker(
    failure_threshold: Optional[int] = None, cooldown_period: Optional[float] = None,
    cooldown_seconds: Optional[float] = None, cooldown_window_seconds: Optional[float] = None,
) -> HardwareCircuitBreaker:
    return HardwareCircuitBreaker.get_instance(
        failure_threshold=failure_threshold, cooldown_period=cooldown_period,
        cooldown_seconds=cooldown_seconds, cooldown_window_seconds=cooldown_window_seconds,
    )
