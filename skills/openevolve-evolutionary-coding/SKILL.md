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

# What is OpenEvolve

OpenEvolve is a powerful, Gemini-powered evolutionary coding agent designed to autonomously optimize code, discover advanced algorithms, and engineer complex mathematical solutions. It merges the creative breadth and depth of state-of-the-art Large Language Models (e.g., Gemini Flash for exploring broad ideas and Gemini Pro for deep, insightful suggestions) with automated evaluators. By treating the LLM as an intelligent "genetic operator," it mutates, crosses-over, and iteratively refines entire codebases across hundreds of generations. 

### What OpenEvolve Can Help With
OpenEvolve excels at solving non-differentiable, highly complex problems in computer science and mathematics that standard optimization techniques cannot easily address. It is specifically designed to help you:
- Discover novel algorithmic heuristics for NP-hard problems and operations scheduling.
- Optimize hardware design and low-level compute instructions (e.g., Verilog, GPU/Metal kernels).
- Enhance AI training and inference by finding smarter algorithm division strategies (e.g., Matrix Multiplication, FlashAttention).
- Generate self-improving code that learns from its own runtime errors and execution traces to push past known mathematical bounds.

### How it Defines `eval fitness`
Fitness in OpenEvolve is objective and quantifiable, strictly defined by the `evaluator.py` file. The engine verifies, runs, and scores the proposed programs using automated evaluation metrics. For every generated program, the evaluator returns an `EvaluationResult` contract containing:
- **`metrics`**: A dictionary of float values. The most critical metric is the `combined_score`, acting as the primary fitness signal for selection. Orthogonal metrics (like `speed` and `accuracy`) are mapped to the MAP-Elites grid to maintain a diverse population of elite solutions.
- **`artifacts`**: A side-channel dictionary capturing standard output, tracebacks, or specific logic failures. These artifacts are fed *back* into the LLM during the next generation, providing intelligent feedback so the agent can self-correct and verify answers.

### How it Optimizes Domain-Specific Code
OpenEvolve is domain-agnostic; its behavior adapts based on your evaluator design. To optimize code in a specific domain, you craft an automated environment:
- **Data Center & Ecosystem Orchestration**: The evaluator tests scheduling heuristics for systems like Borg to increase worldwide compute resource recovery.
- **Hardware & Compute Kernel Tuning**: The evaluator compiles code (e.g., C++, Rust, or Verilog) in a sandboxed subprocess and strictly measures execution speed (FLOPs/sec) to drive the LLM toward faster, human-readable implementations.
- **Competitive Programming & Mathematics**: The evaluator feeds hidden test cases or open mathematical constraints into the program, utilizing multi-stage "cascade evaluation" to quickly filter out syntactically invalid solutions before running deep, expensive optimization steps.

### What Has Been Achieved So Far
Through its evolutionary architecture, OpenEvolve (and its underlying research basis, AlphaEvolve) has powered massive real-world breakthroughs across complex domains:
- **Data Center Scheduling**: Discovered heuristics for Google's Borg that recover ~0.7% of worldwide compute resources.
- **Hardware & Chip Design**: Proposed functional Verilog rewrites for matrix multiplication circuits integrated into upcoming TPUs.
- **AI Kernel Optimization**: Achieved up to 32.5% speedups for FlashAttention kernels and sped up Gemini's matrix multiplication kernel by 23% (reducing training time by 1%).
- **Advanced Mathematics**: Rediscovered SOTA solutions for ~75% of 50 open mathematical problems, and established a new lower bound in 11 dimensions for the famous kissing number problem.
- **Algorithmic Discovery**: Discovered a novel algorithm to multiply 4x4 complex-valued matrices using only 48 scalar multiplications, improving upon Strassen’s 1969 algorithm.
- **Computational Geometry (`circle_packing`)**: Matched and exceeded AlphaEvolve benchmarks by autonomously discovering novel heuristic placements for packing circles to maximize radii.
- **LLM Prompt Engineering (`llm_prompt_optimization`)**: Systematically evolved and discovered highly complex meta-prompts across massive datasets, drastically improving LLM reasoning performance.
- **Competitive Programming (`online_judge_programming`)**: Autonomously evolved Python and Rust code capable of passing strict, unseen hidden test cases on elite competitive programming platforms.
- **Non-Convex Optimization (`function_minimization`)**: Engineered search algorithms capable of consistently escaping deep local minima in highly non-convex mathematical spaces.

## When to Activate This Skill

Use this skill when:
- User Want to evalute specefic fitness function for specefic program
- Setting up a new OpenEvolve evolution run.
- Writing or debugging `config.yaml`.
- Writing or debugging `evaluator.py`.
- Integrating with Nvidia NIM, OpenRouter, Gemini, DeepSeek, or any non-OpenAI provider.
- Designing multi-stage evaluation.
- Using artifact side-channels for LLM feedback.

---


## Part 1: OpenevolveTool Usage Examples

The `OpenevolveTool` is the core dispatcher for managing OpenEvolve projects. You can execute actions using the `human-skills` command.

**1. Install or Upgrade OpenEvolve Engine:**
Run this command if the OpenEvolve library is not installed or needs to be updated to the latest version.
```bash
human-skills '{
    "tool_name": "OpenevolveTool",
    "tool_args": {
        "action": "install"
    }
}'
# To upgrade an existing installation:
human-skills '{
    "tool_name": "OpenevolveTool",
    "tool_args": {
        "action": "upgrade"
    }
}'
```

**2. Initialize a new project:**
Use this command ONLY when starting a completely fresh evolutionary project from scratch. 
**Note:** This command will fail to execute if the target directory already contains core project files (`config.yaml`, `initial_program.py`, or `evaluator.py`) to prevent overwriting existing work.
```bash
human-skills '{
    "tool_name": "OpenevolveTool",
    "tool_args": {
        "action": "init",
        "path": "/path/to/workspace",
        "project_dir": "my_new_project"
    }
}'
```

**3. Run the evolution engine:**
```bash
human-skills '{
    "tool_name": "OpenevolveTool",
    "tool_args": {
        "action": "run",
        "path": "/path/to/workspace/my_new_project",
        "max_iterations": 50
    }
}'
```

**4. List built-in examples:**
Executing this command returns a verified list of all available example projects (those guaranteed to contain both `evaluator.py` and `config.yaml`). This gives the agent a precise list of valid examples to explore.
```bash
human-skills '{
    "tool_name": "OpenevolveTool",
    "tool_args": {
        "action": "list_example"
    }
}'
```

**5. View specific example:**
Use this command to print the exact `evaluator.py` and `config.yaml` source code directly to the terminal. You should view multiple different examples from the list to fully understand various fitness function logic, configurations, and side-channel artifact implementations before writing your own.

> [!IMPORTANT]
> **MANDATORY REVIEW (The "Expensive 5")**
> You MUST execute the `show_example` command to view the following 5 specific examples before attempting to design complex evaluators. These represent the most advanced and robust setups in OpenEvolve:
> 1. `function_minimization` (Cascade evaluation & MAP-Elites feature dimensions)
> 2. `circle_packing_with_artifacts` (Deep artifact side-channels & Multi-phase config)
> 3. `llm_prompt_optimization` (Prompt evolution over external LLM APIs)
> 4. `attention_optimization` (Hardware-level performance & compute tuning)
> 5. `online_judge_programming` (Test-case driven evaluation & sandboxing)

```bash
human-skills '{
    "tool_name": "OpenevolveTool",
    "tool_args": {
        "action": "show_example",
        "example_view": "online_judge_programming"
    }
}'
```

## Part 2: Evaluator Architecture Patterns

OpenEvolve calls `evaluate(program_path)` on each generated file. The function signature is fixed. metrics: dict of named float scores. MUST include `combined_score`. The keys in metrics should match `feature_dimensions` in config if you use MAP-Elites. artifacts: dict of string key → string/dict value. Artifacts are passed BACK to the LLM as context for its next mutation attempt.


### The `EvaluationResult` Contract

```python
from openevolve.evaluation_result import EvaluationResult

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

If the self-test passes, you can proceed to run the full evolution engine:
```bash
human-skills '{
    "tool_name": "OpenevolveTool",
    "tool_args": {
        "action": "run",
        "path": "/path/to/your/project",
        "max_iterations": 50
    }
}'
```

---

### Critical Rules

| Wrong | Correct | Why |
|---|---|---|
| `llm.model:` | `llm.primary_model:` | `model` key is IGNORED by the config parser |
| No `api_base` for Nvidia/OpenRouter | Must provide `api_base` | Client defaults to OpenAI endpoint |
| Parent `/checkpoints` dir in CLI | Specific `/checkpoint_N` folder | Resuming from parent loads 0 programs/fails |
| `early_stopping_patience: int` | `early_stopping_patience: null` | RL breakthroughs happen late; stops kill runs |
| `diff_based_evolution: false` | `diff_based_evolution: true` | Diff-based is safer for iterative refinement |

## Summary: The Non-Negotiable Rules

1. **Config key is `primary_model`**, never `model`.
2. **Always set `api_base`** for any non-OpenAI endpoint.
3. **`feature_dimensions` names must exactly match metric keys** returned by your evaluator.
4. **Evaluator must never crash** — catch all exceptions, return `combined_score: 0.0`.
5. **Use `EvaluationResult`** with `artifacts` so the LLM can read its own errors.
6. **Implement `evaluate_stage1`** if `cascade_evaluation: true` in config.
7. **Use subprocess isolation** for heavy/untrusted generated programs (infinite loop protection).
8. **Test evaluator standalone** before starting a 200-iteration evolution run.
