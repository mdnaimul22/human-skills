# Universal Evaluator — Operational & Usage Guide

This guide describes how to configure, integrate, and operate the **Universal Evaluator** in automated coding pipelines and evolutionary algorithms (such as OpenEvolve).

---

## 1. Environment & Credentials Setup

The Universal Evaluator communicates with the remote **Laya System 1 Decision Engine** for semantic reasoning. Configure the following environment variables:

```bash
# Required for JevJudge remote semantic judging
export LAYA_API_KEY="sk-9405ffec0936cb65-c598e2-30b6f2b0"

# Optional overrides (defaults shown below)
export LAYA_ENDPOINT="https://momen-gpu.tail374b2b.ts.net:8020/predict"
export LAYA_MODEL="typed-decisions"
export LAYA_TIMEOUT="10.0"
```

> **Security Mandate**: Never hardcode API keys into `evaluation.json`, `spec.json`, or Git tracked code. The client automatically reads `LAYA_API_KEY` from the system environment.

---

## 2. Anatomy of an `EvaluationSpec`

The evaluation specification (`spec.json` or `evaluation.json`) is the single source of truth for an evaluation task.

```json
{
  "evaluation_id": "python-sort-v1",
  "objective": "Implement an optimal O(N log N) in-place or stable sorting algorithm in Python",
  "limits": {
    "timeout_seconds": 30.0,
    "memory_mb": 1024,
    "output_kb": 256
  },
  "collectors": [
    {
      "id": "build_check",
      "type": "build"
    },
    {
      "id": "unit_tests",
      "type": "test"
    },
    {
      "id": "exec_runtime",
      "type": "runtime"
    }
  ],
  "fitness": {
    "metrics": [
      {
        "id": "test_pass_rate",
        "direction": "maximize",
        "weight": 0.6,
        "normalization": {
          "minimum": 0.0,
          "maximum": 1.0
        },
        "constraint": {
          "minimum": 1.0,
          "hard": true
        }
      },
      {
        "id": "sorting_efficiency",
        "direction": "maximize",
        "weight": 0.25,
        "normalization": {
          "minimum": 0.0,
          "maximum": 2.0
        },
        "source": {
          "kind": "judgment",
          "question_id": "sorting_efficiency"
        }
      },
      {
        "id": "runtime_ms",
        "direction": "minimize",
        "weight": 0.15,
        "normalization": {
          "minimum": 0.0,
          "maximum": 1000.0
        }
      }
    ]
  },
  "judge_questions": [
    "Is the candidate code clean, robust, and free of cheat hacks?",
    {
      "id": "sorting_efficiency",
      "type": "score",
      "instructions": "Rate the algorithmic complexity and time efficiency of the candidate source code",
      "criteria": [
        "poor (nested quadratic O(N^2) loops)",
        "moderate (acceptable linearithmic sort)",
        "optimal (highly optimized or vectorized)"
      ]
    }
  ]
}
```

---

## 3. Integrating with OpenEvolve

The Universal Evaluator provides a dedicated bridge (`OpenEvolveBridge`) that maps evaluation runs to OpenEvolve's native `EvaluationResult` interface.

### Pattern 1: Using `make_evaluator` Factory
If configuring an OpenEvolve YAML or pipeline script:

```python
from evaluator.bridge import make_evaluator

# Create an OpenEvolve-compatible evaluation callable
evaluator_fn = make_evaluator(
    spec_path="spec.json",
    support_map={"tests": "tests"},
    entrypoint="main.py",
)

# OpenEvolve invokes the function for each evolved candidate file
result = evaluator_fn("workdir/candidate_0042.py")

print("Combined Fitness :", result.metrics["combined_score"])
print("Is Valid Solution:", bool(result.metrics["valid"]))
print("Artifacts / Logs :", result.artifacts)
```

---

### Pattern 2: Multi-Stage Evaluation in Evolutionary Loops
To maximize throughput, execute Stage 1 gatekeeping before full evaluation:

```python
from pathlib import Path
from evaluator.bridge import OpenEvolveBridge

bridge = OpenEvolveBridge(
    spec="spec.json",
    support_map={"tests": "tests"},
    entrypoint="main.py",
)

candidate_file = Path("mutations/c_120.py")

# Step 1: Run Stage 1 Fast Gatekeeper (~1.5ms)
s1_result = bridge.evaluate_stage1(candidate_file)

if s1_result.metrics.get("valid", 0.0) == 0.0:
    # Reject immediately — save compute and avoid judge overhead
    print("Rejected at Stage 1:", s1_result.artifacts.get("failure_reasons"))
    final_result = s1_result
else:
    # Step 2: Run Full Stage 2 Deep Evaluation
    final_result = bridge.evaluate(candidate_file)
    print("Fitness Score:", final_result.metrics["combined_score"])
```

---

## 4. Sandboxing in Production: Host vs Docker

By default, the evaluator uses `HostSandbox`. When running arbitrary code from LLMs or untrusted genetic mutations, configure `DockerSandbox`:

```python
from evaluator.bridge import OpenEvolveBridge
from evaluator.sandbox.docker import DockerSandbox

# Configure hardened container isolation
secure_sandbox = DockerSandbox(
    image="python:3.11-slim",
    memory_limit="512m",
    cpu_limit="1.0",
    pids_limit=100,
)

bridge = OpenEvolveBridge(
    spec="spec.json",
    support_map={"tests": "tests"},
    entrypoint="main.py",
    sandbox=secure_sandbox,
)
```

With `DockerSandbox` enabled:
- Network access is completely disabled (`--network none`).
- The root filesystem is mounted read-only (`--read-only`).
- All Linux capabilities are dropped (`--cap-drop ALL`).
- CPU, memory, and fork bombs are strictly throttled.

---

## 5. Diagnostic Artifacts & Inspection

When `bridge.evaluate()` executes, it populates `EvaluationResult.artifacts` with diagnostic details:

| Artifact Key | Example Content | Purpose |
| :--- | :--- | :--- |
| `judge_<question_id>` | `score=1.4339 conf=0.5213` | Typed response returned by Laya ModernBERT for the question. |
| `failure_reasons` | `constraint failed: test_pass_rate < minimum 1.0` | Exact explanation if the candidate failed invariant checks. |
| `suggestion` | `Hard constraint violation: ...` | High-level suggestion for agent prompt refinement or debugging. |
| `e_<collector_id>_stderr` | `Traceback (most recent call last)...` | Process error stream if a collector command encountered failures. |
