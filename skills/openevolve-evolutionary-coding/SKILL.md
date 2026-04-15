---
name: "openevolve-evolutionary-coding"
description: "OpenEvolve framework for autonomous code optimization using LLM-driven evolutionary algorithms. Use when working with evolutionary coding, MAP-Elites, code optimization, or creating self-improving programs."
version: "1.0.0"
author: "Human Skill Team"
tags: ["evolution", "optimization", "llm", "code-generation", "map-elites", "machine-learning"]
trigger_patterns:
 - "openevolve"
 - "evolutionary coding"
 - "code optimization"
 - "map-elites"
 - "evolve code"
 - "optimize algorithm"
 - "self-improving code"
 - "nvidia nim"
 - "openrouter evolution"
---

## When to Activate This Skill

Use this skill when:
- Setting up a new OpenEvolve evolution run.
- Writing or debugging `config.yaml`.
- Writing or debugging `evaluator.py`.
- Integrating with Nvidia NIM, OpenRouter, Gemini, DeepSeek, or any non-OpenAI provider.
- Designing multi-stage (cascade) evaluation.
- Implementing MAP-Elites quality-diversity with custom feature dimensions.
- Using artifact side-channels for LLM feedback.

---

## Part 1: The Canonical Configuration Schema

This is the #1 source of bugs. The schema is strict. Violating it silently breaks the run.

### Critical Rules (Learned the Hard Way)

| Wrong | Correct | Why |
|---|---|---|
| `llm.model:` | `llm.primary_model:` | `model` key is IGNORED by the config parser |
| No `api_base` for Nvidia/OpenRouter | Must provide `api_base` | Client defaults to OpenAI endpoint |
| Parent `/checkpoints` dir in CLI | Specific `/checkpoint_N` folder | Resuming from parent loads 0 programs/fails |
| `early_stopping_patience: int` | `early_stopping_patience: null` | RL breakthroughs happen late; stops kill runs |
| `diff_based_evolution: false` | `diff_based_evolution: true` | Diff-based is safer for iterative refinement |

---

### Full Advanced Configuration Template

```yaml
# ============================================================
# OpenEvolve Full Advanced Config — Production Grade Template
# ============================================================

# --- General Evolution Control ---
max_iterations: 200
checkpoint_interval: 10
log_level: "INFO"
random_seed: 42

# diff_based_evolution:
#   true  → LLM generates a unified diff (good for incremental refinement)
#   false → LLM rewrites the entire file (best for radical changes, constructors)
diff_based_evolution: false

# Max characters the LLM can produce per generation
max_code_length: 50000

# Language hint for LLM (use "text" for prompt evolution, "python" for code, "rs" for Rust)
language: "python"

# Early stopping: stop if score doesn't improve for N iterations
# CRITICAL (RL/Trading): ALWAYS set to null. Patience kills late-stage breakthroughs.
early_stopping_patience: null
convergence_threshold: 0.001
early_stopping_metric: "combined_score"


# --- LLM Configuration ---
# RULE: NEVER use `model:` key at top level. Always use `primary_model` OR `models` list.

llm:
  # -----------------------------------------------
  # Option A: Single Model (simplest setup)
  # -----------------------------------------------
  primary_model: "qwen/qwen3.5-122b-a10b"   # Exact model name for the API endpoint
  api_base: "https://integrate.api.nvidia.com/v1"  # For Nvidia NIM
  api_key: "your-nvidia-api-key"             # Or set NVIDIA_API_KEY env var

  # -----------------------------------------------
  # Option B: Ensemble/Thompson Sampling (advanced)
  # Uncomment to replace Option A above.
  # The framework weights models probabilistically.
  # -----------------------------------------------
  # api_base: "https://openrouter.ai/api/v1"
  # models:
  #   - name: "google/gemini-2.5-flash-lite"
  #     weight: 0.8
  #   - name: "google/gemini-2.5-flash"
  #     weight: 0.2

  # -----------------------------------------------
  # Option C: Single Gemini Direct (no OpenRouter)
  # -----------------------------------------------
  # primary_model: "gemini-2.5-flash-lite"
  # api_base: "https://generativelanguage.googleapis.com/v1beta/openai/"

  # -----------------------------------------------
  # Option D: Rust-style primary/secondary (legacy field style)
  # -----------------------------------------------
  # primary_model: "gemini-flash-lite-latest"
  # primary_model_weight: 0.8
  # secondary_model: "gemini-flash-latest"
  # secondary_model_weight: 0.2
  # api_base: "https://generativelanguage.googleapis.com/v1beta/openai/"

  temperature: 0.7       # Lower = more deterministic; Higher = more creative mutations
  top_p: 0.95
  max_tokens: 16384      # Sufficient for full-file rewrites
  timeout: 300           # Seconds before aborting an LLM call
  retries: 3             # Auto-retry on rate limits or transient errors


# --- Prompt Engineering ---
prompt:
  num_top_programs: 3       # How many elite programs to show the LLM as context
  num_diverse_programs: 2   # How many diverse (non-elite) programs for variety
  include_artifacts: true   # CRITICAL: Passes evaluator error messages back to LLM
  max_artifact_bytes: 20480 # Truncate huge artifacts to ~20KB

  # Inline system message (alternative: use system_message_path: "system_message.txt")
  system_message: |
    You are an expert Python/algorithm optimizer working inside an evolutionary loop.

    Your goal is to improve the provided program to maximize `combined_score`.

    RULES:
    - Return ONLY valid Python code. No markdown, no commentary.
    - Preserve the required function signatures exactly.
    - Read error artifacts carefully — they tell you exactly what failed.
    - If the previous attempt timed out, add an early exit or reduce complexity.
    - If validation failed, read the `suggestion` field in the artifact.


# --- MAP-Elites Population Database ---
database:
  population_size: 100      # Total programs in the archive
  archive_size: 50          # How many elites to preserve
  num_islands: 4            # Parallel independent populations (prevents stagnation)

  # Feature dimensions for MAP-Elites grid.
  # CRITICAL: These names MUST exactly match keys returned in EvaluationResult.metrics.
  # The evaluator must return continuous float values for these; the framework bins them.
  feature_dimensions: ["speed", "accuracy"]
  feature_bins: 10          # Creates a 10x10 diversity grid

  # Selection pressure balance
  elite_selection_ratio: 0.1   # 10% pure elite selection
  exploration_ratio: 0.4       # 40% random/diverse selection
  exploitation_ratio: 0.5      # 50% fitness-proportional selection

  # Island migration (how often best programs from one island go to another)
  migration_interval: 10
  migration_rate: 0.15

  # Novelty detection: skip evaluation of nearly-identical programs
  similarity_threshold: 0.99


# --- Evaluator Engine ---
evaluator:
  timeout: 600              # Hard timeout (seconds) for the entire evaluate() call
  max_retries: 3            # Retry evaluation on transient failures

  # Cascade evaluation: run cheap stage1 first; only proceed to expensive stage2 if it passes.
  # Requires evaluator.py to define evaluate_stage1() and evaluate_stage2().
  cascade_evaluation: true
  cascade_thresholds: [0.5] # stage1 must return combined_score >= 0.5 to proceed

  parallel_evaluations: 4   # How many programs to evaluate concurrently
  enable_artifacts: true    # Allow evaluator to return artifact dicts


# --- Novelty Detection (optional, prevent evaluating near-duplicate programs) ---
novelty:
  enabled: true
  embedding_backend: "local"
  embedding_model: "all-MiniLM-L6-v2"
  similarity_threshold: 0.95
  max_regeneration_attempts: 3
  temperature_increment: 0.15  # Increment temperature if LLM keeps generating duplicates
```

---

## Part 2: Evaluator Architecture Patterns

OpenEvolve calls `evaluate(program_path)` on each generated file. The function signature is fixed.
The evaluator **must never crash** the host process. Catch everything. Return structured results always.

### The `EvaluationResult` Contract

```python
from openevolve.evaluation_result import EvaluationResult

# metrics: dict of named float scores. MUST include `combined_score`.
# The keys in metrics should match `feature_dimensions` in config if you use MAP-Elites.
# artifacts: dict of string key → string/dict value.
# Artifacts are passed BACK to the LLM as context for its next mutation attempt.
return EvaluationResult(
    metrics={
        "combined_score": 0.85,  # PRIMARY metric used for selection
        "speed": 0.9,            # Feature dimension 1
        "accuracy": 0.8,         # Feature dimension 2
    },
    artifacts={
        "stdout": "...",
        "stderr": "IndexError at line 42",
        "failure_stage": "stage2_execution",
        "suggestion": "Your function must return a numpy array, not a list."
    }
)
```

Evaluators may also return plain `dict` (backward compatible), but `EvaluationResult` is preferred for artifact support.

---

### Pattern 1: Subprocess Sandbox Evaluator (General Python Programs)

**Use when**: The generated code is a standalone runnable script. Prevents memory leaks and infinite loops from crashing the evolution engine.

```python
"""
evaluator.py — Subprocess Sandbox Pattern
Runs the generated program in complete isolation with a hard timeout.
Proven in: circle_packing_with_artifacts, rust_adaptive_sort
"""
import os
import sys
import time
import pickle
import tempfile
import traceback
import subprocess
from openevolve.evaluation_result import EvaluationResult


TARGET_VALUE = 2.635  # Define your target


class SubprocessTimeoutError(Exception):
    pass


def run_in_subprocess(program_path: str, timeout_seconds: int = 60):
    """
    Execute the evolved program in an isolated subprocess.
    Returns the result dict or raises on failure/timeout.
    """
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp:
        tmp.write(f"""
import sys, pickle, traceback
sys.path.insert(0, '{os.path.dirname(program_path)}')
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("prog", '{program_path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.run()   # Call the standard entry point
    with open('{tmp.name}.res', 'wb') as f:
        pickle.dump({{'ok': True, 'result': result}}, f)
except Exception as e:
    with open('{tmp.name}.res', 'wb') as f:
        pickle.dump({{'ok': False, 'error': str(e), 'tb': traceback.format_exc()}}, f)
""")
        script_path = tmp.name

    res_path = f"{script_path}.res"
    try:
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise SubprocessTimeoutError(f"Timed out after {timeout_seconds}s")

        if not os.path.exists(res_path):
            raise RuntimeError(f"No result file produced. stderr: {stderr.decode()[:500]}")

        with open(res_path, "rb") as f:
            data = pickle.load(f)

        if not data["ok"]:
            raise RuntimeError(f"Program crashed: {data['error']}\n{data.get('tb', '')}")

        return data["result"], stdout.decode()

    finally:
        for p in [script_path, res_path]:
            if os.path.exists(p):
                os.unlink(p)


def evaluate_stage1(program_path: str) -> EvaluationResult:
    """Quick sanity check — does the program run at all?"""
    try:
        result, stdout = run_in_subprocess(program_path, timeout_seconds=30)
        score = float(result) / TARGET_VALUE
        return EvaluationResult(
            metrics={"combined_score": min(score, 1.0), "speed": 1.0, "accuracy": score},
            artifacts={"stage": "stage1_passed", "stdout": stdout[:500]}
        )
    except SubprocessTimeoutError as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "speed": 0.0, "accuracy": 0.0},
            artifacts={"failure_stage": "stage1_timeout", "stderr": str(e),
                       "suggestion": "Reduce algorithm complexity or add early exit."}
        )
    except Exception as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "speed": 0.0, "accuracy": 0.0},
            artifacts={"failure_stage": "stage1_crash", "stderr": str(e)[:500],
                       "suggestion": "Ensure run() is defined and returns a float."}
        )


def evaluate_stage2(program_path: str) -> EvaluationResult:
    """Full deep evaluation."""
    start = time.time()
    try:
        result, stdout = run_in_subprocess(program_path, timeout_seconds=600)
        elapsed = time.time() - start
        score = float(result) / TARGET_VALUE
        speed = max(0.0, 1.0 - (elapsed / 600.0))
        return EvaluationResult(
            metrics={
                "combined_score": min(score, 1.0),
                "speed": speed,
                "accuracy": score,
                "eval_time": elapsed,
            },
            artifacts={"stdout": stdout[:1000], "execution_time": f"{elapsed:.2f}s"}
        )
    except SubprocessTimeoutError as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "speed": 0.0, "accuracy": 0.0, "eval_time": 600.0},
            artifacts={"failure_stage": "stage2_timeout", "stderr": str(e),
                       "suggestion": "Algorithm exceeded 600s. Simplify convergence logic."}
        )
    except Exception as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "speed": 0.0, "accuracy": 0.0, "eval_time": 0.0},
            artifacts={"failure_stage": "stage2_crash", "stderr": str(e)[:500],
                       "traceback": traceback.format_exc()[:1000]}
        )


def evaluate(program_path: str) -> EvaluationResult:
    """Main entry point — OpenEvolve always calls this."""
    return evaluate_stage2(program_path)
```

---

### Pattern 2: Direct Module Loading Evaluator (Light, In-Process)

**Use when**: The generated code is a library/module with a known function interface, not a standalone script. Faster than subprocess but not isolated.

```python
"""
evaluator.py — Direct importlib Pattern
Loads the generated module in-process, calls a known function.
Proven in: arc_benchmark, k_module_problem, function_minimization
"""
import sys
import time
import traceback
import importlib.util
from openevolve.evaluation_result import EvaluationResult


def load_program(program_path: str):
    """Safely load the generated Python module."""
    spec = importlib.util.spec_from_file_location("evolved_program", program_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["evolved_program"] = module
    spec.loader.exec_module(module)
    return module


def evaluate(program_path: str) -> EvaluationResult:
    """
    Evaluate a program that must define `solve(input_data) -> output`.
    """
    try:
        prog = load_program(program_path)

        # --- Interface validation ---
        if not hasattr(prog, "solve"):
            return EvaluationResult(
                metrics={"combined_score": 0.0, "accuracy": 0.0, "speed": 0.0},
                artifacts={
                    "error_type": "MissingFunction",
                    "error_message": "Program must define a function `solve(input_data)`.",
                    "suggestion": "Add: def solve(input_data): ..."
                }
            )

        # --- Run on test cases ---
        test_cases = [
            ({"x": [1, 2, 3]}, [1, 2, 3]),   # (input, expected_output)
            ({"x": [3, 1, 2]}, [1, 2, 3]),
        ]

        correct = 0
        start = time.time()
        for inp, expected in test_cases:
            output = prog.solve(inp)
            if output == expected:
                correct += 1
        elapsed = time.time() - start

        accuracy = correct / len(test_cases)
        speed = max(0.0, 1.0 - elapsed)  # Normalize: 1s baseline
        combined = accuracy * 0.8 + speed * 0.2

        return EvaluationResult(
            metrics={
                "combined_score": combined,
                "accuracy": accuracy,
                "speed": speed,
            },
            artifacts={
                "correct": correct,
                "total": len(test_cases),
                "eval_time": f"{elapsed:.3f}s"
            }
        )

    except SyntaxError as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "accuracy": 0.0, "speed": 0.0},
            artifacts={
                "failure_stage": "syntax_error",
                "stderr": str(e),
                "suggestion": f"Fix syntax error at line {e.lineno}: {e.msg}"
            }
        )
    except Exception as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "accuracy": 0.0, "speed": 0.0},
            artifacts={
                "failure_stage": "runtime_crash",
                "stderr": str(e)[:500],
                "traceback": traceback.format_exc()[:1000]
            }
        )
```

---

### Pattern 3: Deterministic Operation-Count Evaluator (Algorithm Benchmarking)

**Use when**: You need 100% reproducible scores for algorithmic optimizations. Wall-clock time (`time.time()`) is noisy and system-dependent. Counting FLOPs is exact.

```python
"""
evaluator.py — Deterministic Operation Counting Pattern
Mocks numpy operations to count FLOPs exactly instead of timing.
Proven in: memory_search_opt
"""
import sys
import random
import traceback
import numpy as np
import importlib.util
from openevolve.evaluation_result import EvaluationResult

# --- Reproducible fixed seeds ---
FIXED_SEED = 42
random.seed(FIXED_SEED)
np.random.seed(FIXED_SEED)

# --- Operation counter ---
class OpCounter:
    def __init__(self): self.flops = 0; self.comparisons = 0

    def reset(self): self.flops = 0; self.comparisons = 0

    def add_flops(self, n): self.flops += n

    def add_comparison(self): self.comparisons += 1

    def total(self):
        return self.flops + 2 * self.comparisons


counter = OpCounter()

# --- Save originals BEFORE patching (prevents infinite recursion) ---
_orig_dot = np.dot
_orig_norm = np.linalg.norm

def _tracked_dot(a, b):
    counter.add_flops(3 * len(a))  # 2n multiplications + n-1 additions ≈ 3n
    return _orig_dot(a, b)

def _tracked_norm(x):
    counter.add_flops(2 * len(x) + 1)  # x^2 + sum + sqrt
    return _orig_norm(x)

# Apply mock
np.dot = _tracked_dot
np.linalg.norm = _tracked_norm


def generate_test_vectors(n: int = 1000, dim: int = 768) -> list:
    """Generate deterministic test data."""
    random.seed(FIXED_SEED)
    np.random.seed(FIXED_SEED)
    vecs = []
    for i in range(n):
        v = np.random.randn(dim).astype(np.float32)
        norm = _orig_norm(v)
        vecs.append(v / norm if norm > 0 else v)
    return vecs


def evaluate(program_path: str) -> EvaluationResult:
    """Score algorithm by FLOP count. Fewer FLOPs = higher score."""
    try:
        spec = importlib.util.spec_from_file_location("evolved_alg", program_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["evolved_alg"] = mod
        spec.loader.exec_module(mod)

        if not hasattr(mod, "search"):
            return EvaluationResult(
                metrics={"combined_score": 0.0, "speed": 0.0, "accuracy": 0.0},
                artifacts={"error": "Must define search(query_vec, database) -> list"}
            )

        # --- Test 1: Small (100 vectors) ---
        db_small = generate_test_vectors(100)
        query = generate_test_vectors(1)[0]
        counter.reset()
        mod.search(query, db_small)
        ops_small = counter.total()
        baseline_small = 100 * 768 * 3
        score_small = min(1.0, baseline_small / max(ops_small, 1))

        # --- Test 2: Large (5000 vectors) ---
        db_large = generate_test_vectors(5000)
        counter.reset()
        mod.search(query, db_large)
        ops_large = counter.total()
        baseline_large = 5000 * 768 * 3
        score_large = min(1.0, baseline_large / max(ops_large, 1))

        # --- Accuracy check ---
        known_vec = generate_test_vectors(1)[0]
        result = mod.search(known_vec, [known_vec] + generate_test_vectors(50))
        accuracy = 1.0 if (result and np.allclose(result[0], known_vec, atol=1e-5)) else 0.0

        combined = score_small * 0.3 + score_large * 0.5 + accuracy * 0.2

        return EvaluationResult(
            metrics={
                "combined_score": combined,
                "speed": score_large,
                "accuracy": accuracy,
            },
            artifacts={
                "ops_small": ops_small,
                "ops_large": ops_large,
                "baseline_large": baseline_large,
                "speedup": f"{baseline_large / max(ops_large, 1):.2f}x",
            }
        )

    except Exception as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "speed": 0.0, "accuracy": 0.0},
            artifacts={"stderr": str(e), "traceback": traceback.format_exc()[:800]}
        )
```

---

### Pattern 4: Two-Stage Cascade with Geometric Validation

**Use when**: The solution has hard structural constraints that cheap validation can enforce before expensive optimization scoring runs. (E.g., "circles must not overlap before measuring packing quality.")

```python
"""
evaluator.py — Cascade Geometric Validation Pattern
Stage 1: Validate structure cheaply (no overlaps, in-bounds).
Stage 2: Full quality scoring.
Proven in: circle_packing, circle_packing_with_artifacts
"""
import numpy as np
import traceback
from openevolve.evaluation_result import EvaluationResult

TARGET_N = 26
TARGET_SUM = 2.635  # AlphaEvolve benchmark


def _zero_result(reason: str, stage: str) -> EvaluationResult:
    return EvaluationResult(
        metrics={"combined_score": 0.0, "validity": 0.0, "radius_variance": 0.0, "spatial_spread": 0.0},
        artifacts={"failure_stage": stage, "reason": reason,
                   "suggestion": "Ensure centers (26,2) and radii (26,) with no overlap and within unit square."}
    )


def _validate(centers: np.ndarray, radii: np.ndarray):
    """Returns (is_valid, error_message)."""
    if centers.shape != (TARGET_N, 2) or radii.shape != (TARGET_N,):
        return False, f"Shape mismatch: centers={centers.shape}, radii={radii.shape}"
    for i in range(TARGET_N):
        x, y, r = centers[i, 0], centers[i, 1], radii[i]
        if x - r < -1e-6 or x + r > 1 + 1e-6 or y - r < -1e-6 or y + r > 1 + 1e-6:
            return False, f"Circle {i} out of bounds"
    for i in range(TARGET_N):
        for j in range(i + 1, TARGET_N):
            dist = np.linalg.norm(centers[i] - centers[j])
            if dist < radii[i] + radii[j] - 1e-6:
                return False, f"Circles {i} and {j} overlap"
    return True, ""


def _compute_features(centers, radii, valid):
    radius_variance = float(min(1.0, max(0.0, np.var(radii) / 0.0625))) if valid else 0.0
    centroid = np.mean(centers, axis=0)
    dists = np.linalg.norm(centers - centroid, axis=1)
    spatial_spread = float(min(1.0, max(0.0, np.std(dists) / (0.5 * np.sqrt(2))))) if valid else 0.0
    return radius_variance, spatial_spread


def evaluate_stage1(program_path: str) -> EvaluationResult:
    """Fast structural validation only."""
    try:
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location("prog", program_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["prog"] = mod
        spec.loader.exec_module(mod)

        if not hasattr(mod, "run_packing"):
            return _zero_result("run_packing() not defined.", "stage1_interface")

        centers, radii, _ = mod.run_packing()
        centers = np.array(centers)
        radii = np.array(radii)

        valid, err = _validate(centers, radii)
        rv, ss = _compute_features(centers, radii, valid)
        score = (np.sum(radii) / TARGET_SUM) if valid else 0.0

        return EvaluationResult(
            metrics={"combined_score": score, "validity": 1.0 if valid else 0.0,
                     "radius_variance": rv, "spatial_spread": ss},
            artifacts={"validation_error": err} if err else {"status": "stage1_passed"}
        )
    except Exception as e:
        return _zero_result(str(e)[:500], "stage1_crash")


def evaluate_stage2(program_path: str) -> EvaluationResult:
    """Full quality scoring."""
    return evaluate(program_path)


def evaluate(program_path: str) -> EvaluationResult:
    """Full evaluation with geometric scoring."""
    try:
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location("prog", program_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["prog"] = mod
        spec.loader.exec_module(mod)

        centers, radii, _ = mod.run_packing()
        centers, radii = np.array(centers), np.array(radii)

        valid, err = _validate(centers, radii)
        rv, ss = _compute_features(centers, radii, valid)
        sum_r = float(np.sum(radii)) if valid else 0.0
        score = sum_r / TARGET_SUM if valid else 0.0

        return EvaluationResult(
            metrics={
                "combined_score": min(score, 1.0),
                "validity": 1.0 if valid else 0.0,
                "sum_radii": sum_r,
                "radius_variance": rv,
                "spatial_spread": ss,
            },
            artifacts={
                "packing_ratio": f"{score:.4f}",
                "validation_error": err if err else "None",
            }
        )
    except Exception as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "validity": 0.0, "radius_variance": 0.0, "spatial_spread": 0.0},
            artifacts={"failure_stage": "evaluate_crash", "stderr": str(e)[:500],
                       "traceback": traceback.format_exc()[:800]}
        )
```

---

### Pattern 5: External Compiler Evaluator (Rust / Native Code)

**Use when**: The evolved program is in a compiled language (Rust, C, etc.). Requires `cargo` or `gcc` in PATH.

```python
"""
evaluator.py — External Compiler Pattern
Compiles the evolved Rust/C program, runs the binary, parses JSON output.
Proven in: rust_adaptive_sort
"""
import json
import asyncio
import subprocess
import tempfile
from pathlib import Path
from openevolve.evaluation_result import EvaluationResult


def evaluate(program_path: str) -> EvaluationResult:
    return asyncio.run(_async_evaluate(program_path))


async def _async_evaluate(program_path: str) -> EvaluationResult:
    try:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "evolved_proj"

            # Initialize cargo project
            init = subprocess.run(
                ["cargo", "init", "--name", "evolved_proj", str(proj)],
                capture_output=True, text=True
            )
            if init.returncode != 0:
                return EvaluationResult(
                    metrics={"combined_score": 0.0, "correctness": 0.0},
                    artifacts={"error": "cargo init failed", "stderr": init.stderr[:400]}
                )

            # Write evolved code as lib.rs
            (proj / "src" / "lib.rs").write_text(Path(program_path).read_text())

            # Build
            build = subprocess.run(
                ["cargo", "build", "--release"], cwd=proj,
                capture_output=True, text=True, timeout=60
            )
            if build.returncode != 0:
                return EvaluationResult(
                    metrics={"combined_score": 0.0, "correctness": 0.0, "compile_success": 0.0},
                    artifacts={"error": "Compilation failed", "stderr": build.stderr[:800],
                               "suggestion": "Fix Rust compile errors above."}
                )

            # Run
            run = subprocess.run(
                ["cargo", "run", "--release"], cwd=proj,
                capture_output=True, text=True, timeout=30
            )
            if run.returncode != 0:
                return EvaluationResult(
                    metrics={"combined_score": 0.0, "correctness": 0.0, "compile_success": 1.0},
                    artifacts={"error": "Runtime panic", "stderr": run.stderr[:400]}
                )

            # Parse JSON output from binary
            out = run.stdout
            data = json.loads(out[out.find("{"):out.rfind("}") + 1])
            correctness = data["correctness"]
            perf = data["performance_score"]
            adapt = data.get("adaptability_score", 0.5)
            score = (0.6 * perf + 0.4 * adapt) if correctness >= 1.0 else 0.0

            return EvaluationResult(
                metrics={"combined_score": score, "correctness": correctness,
                         "speed": perf, "accuracy": adapt, "compile_success": 1.0},
                artifacts={"raw_times": str(data.get("times", []))}
            )

    except subprocess.TimeoutExpired:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "correctness": 0.0},
            artifacts={"error": "Compilation or execution timed out."}
        )
    except Exception as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "correctness": 0.0},
            artifacts={"error": str(e)[:500]}
        )
```

---

## Part 3: Quick Start Workflow

```bash
# Navigate to your project
cd /path/to/your/project

# Activate the correct Python env (openevolve must be installed)
source .venv/bin/activate

# Create the minimum required files:
# - initial_program.py   (your starting code)
# - evaluator.py         (scoring logic, must define evaluate())
# - config.yaml          (from the template above)

# Run evolution
python /path/to/openevolve/openevolve-run.py \
    initial_program.py \
    evaluator.py \
    --config config.yaml \
    --iterations 50

```

---

## Part 4: API Endpoints Reference

| Provider | `api_base` | Notes |
|---|---|---|
| OpenAI (default) | (omit) | Uses official OpenAI client |
| Nvidia NIM | `https://integrate.api.nvidia.com/v1` | Model: `qwen/qwen3.5-122b-a10b` |
| OpenRouter | `https://openrouter.ai/api/v1` | Model: `google/gemini-2.5-flash-lite` |
| Gemini Direct | `https://generativelanguage.googleapis.com/v1beta/openai/` | Model: `gemini-2.5-flash-lite` |
| DeepSeek | `https://api.deepseek.com/v1` | Model: `deepseek-reasoner` |
| Local (vLLM) | `http://localhost:8000/v1` | Any local model |

> **Nvidia NIM Model Names**: Do NOT prefix with `openai/`. Use exactly `qwen/qwen3.5-122b-a10b`.

---

## Part 5: Troubleshooting Checklist

**Evolution produces `Score=0` every generation:**
- Ensure your evaluator never raises an uncaught exception.
- Print `EvaluationResult.metrics` in evaluator main block during standalone test.
- Check that the initial program itself scores > 0: `python evaluator.py initial_program.py`.

**`LLM generation failed` in logs:**
- Check `api_base` is set correctly for your provider.
- Verify `api_key` is set (env var or field in config).
- Confirm model name exactly matches the provider's API (no `openai/` prefix for Nvidia NIM).
- Reduce `parallel_evaluations` to 1 to isolate API quota errors.

**Cascade evaluation never reaches stage2:**
- Lower `cascade_thresholds` temporarily (e.g., `[0.1]`).
- Add print statements inside `evaluate_stage1` and check logs.
- Confirm your `evaluate_stage1` function IS defined in evaluator.py.

**MAP-Elites feature dimensions not populating:**
- Ensure the keys in `feature_dimensions` config exactly match keys in `EvaluationResult.metrics`.
- Values must be continuous floats in [0, 1]. The framework bins them — do not pre-bin.

**No diversity, population converges too fast:**
- Increase `temperature` (0.9–1.0).
- Raise `exploration_ratio` to 0.5+.
- Add more `num_islands`.
- Enable novelty detection (`novelty.enabled: true`).

---

## Part 6: Evaluator Self-Test Template

Always test your evaluator standalone before running evolution:

```python
# At the bottom of evaluator.py:
if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "initial_program.py"

    print("=== Stage 1 ===")
    r1 = evaluate_stage1(path)
    print(f"  Metrics:   {r1.metrics}")
    print(f"  Artifacts: {r1.artifacts}")

    print("=== Stage 2 / Full ===")
    r2 = evaluate(path)
    print(f"  Metrics:   {r2.metrics}")
    print(f"  Artifacts: {r2.artifacts}")

    assert "combined_score" in r2.metrics, "combined_score MISSING from metrics!"
    print("\nAll checks passed.")
```

Run as: `python evaluator.py initial_program.py`

---

## Summary: The Non-Negotiable Rules

1. **Config key is `primary_model`**, never `model`.
2. **Always set `api_base`** for any non-OpenAI endpoint.
3. **`feature_dimensions` names must exactly match metric keys** returned by your evaluator.
4. **Evaluator must never crash** — catch all exceptions, return `combined_score: 0.0`.
5. **Use `EvaluationResult`** with `artifacts` so the LLM can read its own errors.
6. **Implement `evaluate_stage1`** if `cascade_evaluation: true` in config.
7. **Use subprocess isolation** for heavy/untrusted generated programs (infinite loop protection).
8. **Test evaluator standalone** before starting a 200-iteration evolution run.
