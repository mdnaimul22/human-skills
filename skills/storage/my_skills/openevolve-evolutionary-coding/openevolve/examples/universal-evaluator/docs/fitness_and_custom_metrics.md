# Universal Evaluator — Fitness & Custom Metrics Engineering

This guide details how to customize, extend, and engineer fitness functions for specific coding challenges. It covers declarative in-spec metric definitions, custom Python metric providers, hard constraint invariant defenses, and semantic prompt engineering using the **Laya System 1 Decision Engine**.

---

## 1. Fitness Architecture Overview

The Universal Evaluator completely separates **Evidence Collection** from **Fitness Evaluation**:

```text
Collectors / Sandbox (Raw Data)  ──────┐
                                       ├──> MetricRegistry ──> ConstraintEngine ──> Normalized Weighted Fitness
Laya System 1 Judge (Semantic Choices) ┘
```

This separation guarantees:
1. **Determinism**: Collectors never calculate fitness directly; they only emit typed evidence.
2. **Anti-Cheating**: Remote LLMs or BERT judges cannot assign arbitrary scores; they only answer calibrated typed propositions (`noul`, `choice`, `score`).
3. **Composability**: You can combine runtime benchmarks, unit test outcomes, SQL query correctness, security audits, and neural code reviews into one unified objective function.

---

## 2. Declarative Metric Customization (In `spec.json`)

For most use cases, custom fitness functions can be declared directly in JSON without writing Python code.

### Metric Definition Schema
Every item inside `fitness.metrics` accepts the following attributes:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique metric identifier (e.g. `test_pass_rate`, `runtime_ms`, `algo_score`). |
| `direction` | `"maximize"` \| `"minimize"` | Optimization target. |
| `weight` | `float > 0` | Relative importance. The sum of all metric weights should typically equal `1.0`. |
| `normalization.minimum` | `float` | Lower bound mapped to `0.0` (for maximize) or `1.0` (for minimize). |
| `normalization.maximum` | `float` | Upper bound mapped to `1.0` (for maximize) or `0.0` (for minimize). |
| `constraint.minimum` | `float` | Minimum allowable threshold. |
| `constraint.maximum` | `float` | Maximum allowable threshold. |
| `constraint.hard` | `bool` | If `true`, failing this boundary sets $\text{fitness} = 0.0$ and $\text{valid} = \text{false}$. |
| `source` | `MetricSource` | Optional explicit binding to collector evidence or judge questions. |

---

### Example A: Binding to Collector Evidence
To optimize a metric emitted by a collector (e.g. SQL query latency or test pass rate):

```json
{
  "id": "query_latency_ms",
  "direction": "minimize",
  "weight": 0.3,
  "normalization": {
    "minimum": 0.0,
    "maximum": 500.0
  },
  "constraint": {
    "maximum": 300.0,
    "hard": false
  },
  "source": {
    "kind": "evidence",
    "collector": "sql",
    "field": "latency_ms",
    "aggregation": "mean"
  }
}
```

---

### Example B: Binding to Laya Semantic Judgments
To optimize a semantic quality assessed by Laya ModernBERT:

```json
{
  "id": "code_architecture_score",
  "direction": "maximize",
  "weight": 0.25,
  "normalization": {
    "minimum": 0.0,
    "maximum": 5.0
  },
  "source": {
    "kind": "judgment",
    "question_id": "architecture_rating",
    "field": "value"
  }
}
```

---

## 3. Engineering Laya Semantic Judge Questions

Laya evaluates code using ModernBERT-large (`typed-decisions`). In your spec, define `judge_questions` using three supported typed question structures:

### 1. `noul` (Binary Truth Proposition)
Evaluates whether a statement about the candidate code is true, returning a calibrated probability ($0.0 \le p \le 1.0$):

```json
{
  "id": "is_optimal_complexity",
  "type": "noul",
  "instructions": "Does the implementation achieve O(N log N) complexity without nested loops?"
}
```

### 2. `choice` (Categorical Classification)
Selects the winning category from discrete choices based on criteria definitions:

```json
{
  "id": "algorithm_type",
  "type": "choice",
  "instructions": "Which algorithmic design pattern is implemented in the source code?",
  "criteria": {
    "dynamic_programming": "Memoized table or bottom-up tabulation",
    "divide_and_conquer": "Recursive partitioning (e.g. MergeSort, QuickSort)",
    "brute_force": "Exhaustive permutation or nested iteration",
    "other": "Alternative pattern"
  }
}
```

### 3. `score` (Ordinal / Scaled Evaluation)
Evaluates the candidate against an ordered rubric, returning a continuous score across the levels:

```json
{
  "id": "sorting_efficiency",
  "type": "score",
  "instructions": "Rate the algorithmic efficiency and time complexity of the source code",
  "criteria": [
    "poor (nested quadratic O(N^2) loops or excessive copies)",
    "moderate (linearithmic O(N log N) with minor allocations)",
    "optimal (in-place, vectorized, or native optimized implementation)"
  ]
}
```

---

## 4. Writing a Custom Python Metric Provider

If your evaluation requires custom mathematical algorithms or cross-collector correlation (e.g. measuring FLOPs per memory byte or combining test coverage with cyclomatic complexity), implement a custom `MetricProvider`.

### Step 1: Create the Provider Class
In your project (e.g. `src/custom_metrics.py`):

```python
from evaluator.metrics.base import MetricProvider
from evaluator.models.evidence import Evidence
from evaluator.models.judgment import Judgment
from evaluator.models.metric import MetricValue

class AlgorithmicDensityProvider(MetricProvider):
    name = "algorithmic_density"
    metric_ids = frozenset({"efficiency_density"})

    def supports(self, metric_id: str) -> bool:
        return metric_id in self.metric_ids

    def derive(
        self,
        metric_id: str,
        evidence: list[Evidence],
        judgments: list[Judgment],
    ) -> MetricValue:
        # Extract runtime duration from runtime collector
        runtime_ms = 1.0
        for ev in evidence:
            if ev.collector == "runtime" and ev.status.value == "passed":
                runtime_ms = float(ev.value)
                break

        # Extract semantic efficiency score from Laya judgment
        judge_score = 1.0
        for j in judgments:
            if j.question_id == "sorting_efficiency" and isinstance(j.value, (int, float)):
                judge_score = float(j.value)
                break

        # Custom non-linear formula: Efficiency Density = (JudgeScore^2) / sqrt(RuntimeMs)
        calculated_density = (judge_score ** 2) / (runtime_ms ** 0.5)

        return MetricValue(
            metric_id=metric_id,
            value=float(calculated_density),
            evidence_ids=[ev.id for ev in evidence if ev.collector == "runtime"],
            judgment_ids=["sorting_efficiency"],
            provider=self.name,
            provider_version="1.0.0",
        )
```

### Step 2: Register the Provider in `OpenEvolveBridge`
When instantiating the bridge in your evolutionary loop:

```python
from evaluator.bridge import OpenEvolveBridge
from evaluator.metrics.registry import MetricRegistry
from custom_metrics import AlgorithmicDensityProvider

# Start with canonical metric providers (test_pass_rate, runtime_ms, etc.)
metric_registry = MetricRegistry.canonical()

# Register your custom provider
metric_registry.register(AlgorithmicDensityProvider())

# Inject into the bridge
bridge = OpenEvolveBridge(
    spec="spec.json",
    metric_registry=metric_registry,
    support_map={"tests": "tests"},
    entrypoint="main.py",
)
```

Now, any metric declared in `spec.json` with `id: "efficiency_density"` will be calculated by your custom provider.
