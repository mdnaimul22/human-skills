# Universal Evaluator — Built-in Collectors Catalog

The Universal Evaluator features **13 canonical typed collectors**. Every collector implements the `EvidenceCollector` interface, executes within the configured sandbox, and emits strictly typed `Evidence` models bound to cryptographic provenance.

---

## Collectors Summary Matrix

| Collector | Type Key | Config Model | Capabilities | Canonical Metric(s) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Build** | `"build"` | `CommandCollectorConfig` | `build`, `filesystem` | `compile_success` |
| **2. Test** | `"test"` | `CommandCollectorConfig` | `correctness`, `process` | `test_pass_rate` |
| **3. Runtime** | `"runtime"` | `CommandCollectorConfig` | `runtime`, `process` | `runtime_ms` |
| **4. Benchmark** | `"benchmark"` | `CommandCollectorConfig` | `benchmark`, `process` | Custom throughput / score |
| **5. Static** | `"static"` | `CommandCollectorConfig` | `static`, `filesystem` | Syntax validity (`1.0` / `0.0`) |
| **6. SQL** | `"sql"` | `SQLCollectorConfig` | `sql`, `database` | `query_pass_rate`, `query_latency_ms` |
| **7. Security** | `"security"` | `SecurityCollectorConfig` | `security`, `scanner` | `critical_findings`, `high_findings`, `security_pass` |
| **8. GPU** | `"gpu"` | `GPUCollectorConfig` | `gpu`, `nvidia-smi` | `gpu_latency_ms`, `gpu_memory_mb`, `gpu_throughput` |
| **9. API** | `"api"` | `APICollectorConfig` | `http`, `api` | `api_status_pass_rate`, `api_latency_ms` |
| **10. Coverage** | `"coverage"` | `CoverageCollectorConfig` | `coverage`, `process` | `line_coverage`, `branch_coverage` |
| **11. Dependency** | `"dependency"` | `DependencyCollectorConfig` | `dependency`, `package-metadata` | `vulnerable_dependencies` |
| **12. Resource** | `"resource"` | `ResourceCollectorConfig` | `resource`, `process` | `peak_memory_mb`, `cpu_time_ms`, `wall_time_ms` |
| **13. Artifact** | `"artifact"` | `ArtifactCollectorConfig` | `artifact`, `filesystem` | `artifact_valid` |

---

## Detailed Specifications

### 1. Build Collector (`type: "build"`)
- **Purpose**: Verifies that candidate source code compiles, packages, or builds cleanly.
- **Config Model**: `CommandCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.BUILD`
  - `status`: `PASSED` if exit code is 0; `FAILED` otherwise.
  - `value`: `1.0` (compiled) or `0.0` (failed).
- **Example Spec**:
```json
{
  "id": "build",
  "type": "build",
  "timeout_seconds": 10.0
}
```

---

### 2. Test Collector (`type: "test"`)
- **Purpose**: Executes automated unit/integration test suites (e.g. `pytest`, `unittest`) inside the sandbox.
- **Config Model**: `CommandCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.CORRECTNESS`
  - `status`: `PASSED` if all tests pass; `FAILED` if any test fails.
  - `value`: Pass rate float between `0.0` and `1.0`.
- **Example Spec**:
```json
{
  "id": "test",
  "type": "test",
  "timeout_seconds": 30.0
}
```

---

### 3. Runtime Collector (`type: "runtime"`)
- **Purpose**: Executes candidate code on sample input to measure runtime execution latency.
- **Config Model**: `CommandCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.RUNTIME`
  - `status`: `PASSED` if execution completed within limits.
  - `value`: Duration in milliseconds (`ms`).
  - `unit`: `"ms"`
- **Example Spec**:
```json
{
  "id": "runtime",
  "type": "runtime",
  "timeout_seconds": 5.0
}
```

---

### 4. Benchmark Collector (`type: "benchmark"`)
- **Purpose**: Executes performance benchmarking suites over repeated trials.
- **Config Model**: `CommandCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.RUNTIME`
  - `value`: Benchmarked execution score or operations per second.
- **Example Spec**:
```json
{
  "id": "benchmark",
  "type": "benchmark",
  "timeout_seconds": 60.0
}
```

---

### 5. Static Collector (`type: "static"`)
- **Purpose**: Performs static AST parsing (`py_compile`) and syntax validation without running code.
- **Config Model**: `CommandCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.CORRECTNESS`
  - `value`: `1.0` (valid syntax) or `0.0` (syntax error).
- **Usage**: Used by `evaluate_stage1` as the fast gatekeeper (< 2ms).

---

### 6. SQL Collector (`type: "sql"`)
- **Purpose**: Validates database queries, schema migrations, and SQL logic against an SQLite database.
- **Config Model**: `SQLCollectorConfig`
- **Configuration Fields**:
  - `database`: Database path or `":memory:"`.
  - `setup`: List of initialization SQL DDL statements.
  - `queries`: List of `SQLQuerySpec` (`sql`, `expected_rows`).
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.CORRECTNESS`
  - `value`: Fraction of queries that executed successfully and returned expected row counts (`0.0` to `1.0`).
  - `metadata.latency_ms`: Total execution time for all queries.
- **Example Spec**:
```json
{
  "id": "sql_validator",
  "type": "sql",
  "database": ":memory:",
  "setup": [
    "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, balance REAL);",
    "INSERT INTO users VALUES (1, 'Alice', 100.0), (2, 'Bob', 50.0);"
  ],
  "queries": [
    {
      "sql": "SELECT * FROM users WHERE balance >= 50.0;",
      "expected_rows": 2
    }
  ]
}
```

---

### 7. Security Collector (`type: "security"`)
- **Purpose**: Audits candidate code for security flaws (e.g. SQL injection, command execution, path traversal) using SAST scanners like Bandit.
- **Config Model**: `SecurityCollectorConfig`
- **Configuration Fields**:
  - `tool`: Scanner name (`"bandit"` default).
  - `severity`: Minimum reported threshold (`"low"`, `"medium"`, `"high"`, `"critical"`).
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.QUALITY`
  - `value`: `1.0` (clean) or `0.0` (vulnerabilities found).
  - `metadata.critical_findings`: Count of critical security findings.
  - `metadata.high_findings`: Count of high severity findings.
- **Example Spec**:
```json
{
  "id": "security",
  "type": "security",
  "tool": "bandit",
  "severity": "high"
}
```

---

### 8. GPU Collector (`type: "gpu"`)
- **Purpose**: Queries host NVIDIA GPU hardware accelerators via `nvidia-smi` to monitor CUDA utilization and VRAM consumption.
- **Config Model**: `GPUCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.RUNTIME`
  - `metadata.peak_memory_mb`: Maximum VRAM allocated.
  - `metadata.latency_ms`: Kernel execution duration.
  - `metadata.throughput`: Operations processed per second.
- **Fail-Safe Behavior**: If no NVIDIA GPU is physically present, the collector gracefully records `status: SKIPPED` and `value: 0.0` without fabricating fake metrics.

---

### 9. API Collector (`type: "api"`)
- **Purpose**: Sends HTTP requests against local web endpoints or microservices spawned by the candidate code.
- **Config Model**: `APICollectorConfig`
- **Configuration Fields**:
  - `requests`: List of `APIRequestSpec` (`url`, `method`, `headers`, `json`, `expected_status`).
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.CORRECTNESS`
  - `value`: Fraction of HTTP calls returning `expected_status`.
  - `metadata.latency_ms`: Average network roundtrip latency.
- **Example Spec**:
```json
{
  "id": "api_check",
  "type": "api",
  "requests": [
    {
      "url": "http://127.0.0.1:8000/health",
      "method": "GET",
      "expected_status": 200
    }
  ]
}
```

---

### 10. Coverage Collector (`type: "coverage"`)
- **Purpose**: Calculates line and branch test coverage across the candidate source files.
- **Config Model**: `CoverageCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.QUALITY`
  - `value`: Overall percentage coverage (`0.0` to `100.0`).
  - `metadata.line_coverage`: Percentage of lines covered.
  - `metadata.branch_coverage`: Percentage of branches evaluated.

---

### 11. Dependency Collector (`type: "dependency"`)
- **Purpose**: Scans project manifest (`pyproject.toml`, `requirements.txt`) for unpinned, obsolete, or vulnerable dependencies.
- **Config Model**: `DependencyCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.QUALITY`
  - `value`: `1.0` (safe) or `0.0` (unresolved/vulnerable packages).
  - `metadata.vulnerable_dependencies`: Count of vulnerable packages detected.

---

### 12. Resource Collector (`type: "resource"`)
- **Purpose**: Measures process-level compute consumption using system timers and memory profilers.
- **Config Model**: `ResourceCollectorConfig`
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.RUNTIME`
  - `metadata.peak_memory_mb`: Maximum Resident Set Size (RSS) memory in MB.
  - `metadata.cpu_time_ms`: Total CPU user + sys time.
  - `metadata.wall_time_ms`: Elapsed real-world time.

---

### 13. Artifact Collector (`type: "artifact"`)
- **Purpose**: Verifies that generated output files (e.g. exported datasets, neural weights, plots) exist, match schema rules, and are non-empty.
- **Config Model**: `ArtifactCollectorConfig`
- **Configuration Fields**:
  - `files`: List of `ArtifactFileSpec` (`path`, `format`: `"text" | "json" | "binary"`).
- **Emitted Evidence**:
  - `category`: `EvidenceCategory.QUALITY`
  - `value`: `1.0` if all declared artifacts are present and well-formed; `0.0` otherwise.
