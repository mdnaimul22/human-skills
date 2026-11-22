# system.py DOX

> *`src/apps/system/` acts as the "Central Resource Bank & Hardware Control Plane":*
> *It remains completely agnostic to specific business applications (video transcoding, CV generation, document parsing).*
> *It monitors host CPU, RAM, cgroup limits, and multi-tier GPU/NVENC health, enforces configuration-driven 90% hard usage ceilings from `env/.system`, and issues atomic multi-dimensional capacity permits (`ResourcePermit` + `ResourceLease`).*

## Purpose

- Own the `src/apps/system` platform resource substrate and hardware control plane.
- Detect host CPU topology (physical, logical, cgroup v2 quota, EWMA utilization), memory (total, available, swap, cgroup v2, Vidula process-tree RSS), and multi-tier GPU hardware (`pynvml` primary → `nvidia-smi` fallback incl. WSL2 `/usr/lib/wsl/lib` → VAAPI device check, zero `torch` import) plus one-shot startup FFmpeg NVENC encode canary.
- Enforce configuration-driven resource caps (`Settings.SYSTEM_*`, hot-reloaded at runtime from `env/.system` with atomic Pydantic validation) and fair-share allocation across `UserTier` (`GUEST`, `REGISTERED`, `PREMIUM`) and `LoadLevel` (`NORMAL`, `ELEVATED`, `CRITICAL`, `EMERGENCY`) with damped de-escalation hysteresis.
- Prevent CPU/RAM/GPU/VRAM oversubscription via an atomic resource ledger (`LeaseTracker`) and per-loop FIFO waiter wakeup (`ResourceGovernor`).
- Maintain closed-loop encoder circuit breakers (`HardwareCircuitBreaker`) so failing NVENC executions automatically downgrade hybrid workloads to CPU (`libx264`/`libx265`).
- Emit structured lifecycle observability into `logs/system.log` (`system.startup.*` 4-line inventory banner, `system.load.transition`, `system.gpu.transition`, periodic `system.heartbeat`, `system.config.reloaded`, and `permit.*`/`lease.*` events) mirrored to `logs/telemetry.jsonl`.

## Ownership

- `src/apps/system/manager.py` owns the public facade and lifecycle orchestrator (`SystemManager`, `get_system_manager()`).
- `src/apps/system/helpers/` owns isolated sub-engine workers:
  - `gpu_detector.py` — `GpuDetector` (`pynvml` → `nvidia-smi` → VAAPI + startup NVENC canary + clean shutdown).
  - `probe.py` — `HardwareProbe` (non-blocking sampler, CPU warmup/EWMA, Vidula process-tree RSS, cgroups v2, SHA-256 hardware fingerprint, and leak-free `weakref.WeakKeyDictionary` for event loop locks).
  - `profiler.py` — `HardwareProfiler` (config-driven thresholds, hysteresis `LoadLevel`, orthogonal `GpuHealthState`).
  - `budget.py` — `ResourceBudgetCalculator` & `PermitAllocationDecision` (90% usable ceilings, decomposed sub-atomic thread/RAM calculators with complexity $\le 5$, and fair-share multi-dimensional permit calculation).
  - `allocator.py` — `ResourceAllocator` (8 seeded config-driven workload profiles incl. `egress`, `sync_from_settings()`).
  - `lease_tracker.py` — `LeaseTracker` (atomic multi-dimensional ledger accounting for slots/threads/RAM/GPU sessions/VRAM + TTL reaping, zero legacy aliases).
  - `governor.py` — `ResourceGovernor` (single-step atomic `acquire_resource_permit`, in-place $O(1)$ `_remove_waiter` deque cleanup, unified `evaluate_state()`, and RAM starvation 503 guard).
  - `circuit_breaker.py` — `HardwareCircuitBreaker` (CLOSED/OPEN/HALF_OPEN state machine + `reset_all()` + `list_states()`).
  - `validator.py` — Canonical sync `HardwareValidator` & `ResourceValidator` (re-exported by `src/core/validators/`).
- `src/apps/system/schema/` owns strict Pydantic v2 models:
  - `hardware.py`: `GpuBackend`, `GpuHealthState`, `CpuTelemetry`, `RamTelemetry`, `GpuDeviceTelemetry`, `GpuTelemetry`, `HardwareTelemetrySnapshot`.
  - `resource.py`: `UserTier`, `LoadLevel`, `WorkloadType` (incl. `EGRESS`), `TokenType`, `WorkloadProfile`, `ResourceLease`, `ResourcePermit`, `PermitRequest`, `ResourceCapacity`, `ThrottlingStatus`, `LeaseReapReport`, `ThreadBudgetDecision`, `SystemResourceBudget`, `LedgerCommitmentSnapshot`.
  - `breaker.py`: `CircuitState`, `EncoderCircuitState`.
  - `status.py`: `SystemStatusSnapshot`.
- `src/routers/system.py` exposes `GET /`, `GET /health`, and dev/direct-localhost-only `GET /system/status`.

## Runtime Contracts

- **Configuration Hot-Reload (`env/.system`):** All `SYSTEM_*` settings default to 90% hard usage ceilings (`SYSTEM_MAX_CPU_USAGE_PERCENT=90.0`, `SYSTEM_MAX_RAM_USAGE_PERCENT=90.0`, `SYSTEM_GPU_MAX_VRAM_USAGE_PERCENT=90.0`, `SYSTEM_GPU_MAX_UTIL_PERCENT=90.0`). `SystemManager._sampler_loop()` polls mtime every 2s and calls `Settings.reload_system_env()` + `allocator.sync_from_settings()` atomically, ignoring malformed edits without disturbing live state.
- **Anti-Oversubscription Ledger Invariants:** Active compute leases commit exact `(cpu_cores_allocated, memory_bytes_allocated, gpu_device_id, vram_bytes_allocated)` at admission and decrement them idempotently on `release_permit()` or `reap_expired_leases()`.
- **WSL2 Subprocess Library Injection:** `src/helpers/process_env.py` (`inject_gpu_library_env`) prepends existing dirs from `Settings.SYSTEM_GPU_LIB_DIRS` (`/usr/lib/wsl/lib`) into `LD_LIBRARY_PATH` so systemd services can run NVML and `h264_nvenc` / `hevc_nvenc`.
- **Zero-Trust `/system/status` Gate:** Accessible only when `Settings.is_development` is `True` OR the request arrives directly from loopback (`127.0.0.1` / `::1`) without reverse-proxy forwarding headers (`X-Forwarded-For`, `X-Real-IP`, `Forwarded`); returns HTTP `404` otherwise.
- **Dependency Hygiene & Zero Backward-Compatibility Aliases:** `src/apps/system/` strictly avoids backward-compatibility hacks, legacy property aliases, or arbitrary fallbacks (per project standards). Downstream callers (`EgressManager`, `JobControl`, `JobWorker`, `main.py`, `routers/system.py`) interact strictly through canonical `SystemManager` methods (`acquire_resource_permit`, `release_permit`, `release_permit_by_job_id`); `FFmpegManager` consumes `PermitLike` via IoC. The module never imports `torch`, `src/core/*`, `pathlib.Path` directly, or untyped `Any`/`isinstance`.

## Verification

- AST architecture compliance linter (`0 violations`):
  ```bash
  human-skills '{"tool_name": "linter", "tool_args": {"scan_path": "src/apps/system"}}'
  ```
- Targeted system & caller test suites:
  ```bash
  PYTHONPATH=. pytest tests/apps/system/ tests/helpers/test_process_env.py -v --durations=0
  ```
