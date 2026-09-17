import importlib.util
import os
import numpy as np
from openevolve.evaluation_result import EvaluationResult
from benchmark.synthetic import SyntheticBenchmark
from validation.ranking import kendall_tau_score

def evaluate(program_path: str) -> EvaluationResult:
    metrics = {
        "combined_score": -1.0,
        "kendall_tau": -1.0,
        "violation_rate": 1.0,
    }
    artifacts = {
        "error_type": None,
        "error_message": None,
    }
    bench = SyntheticBenchmark()
    train_data, _ = bench.get_benchmarks()
    target_fn_name = "fitness_function"
    try:
        mod_name = os.path.basename(program_path).replace(".py", "")
        spec = importlib.util.spec_from_file_location(mod_name, program_path)
        if spec is None or spec.loader is None:
            artifacts["error_type"] = "ImportError"
            artifacts["error_message"] = "Cannot load module spec"
            return EvaluationResult(metrics=metrics, artifacts=artifacts)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        artifacts["error_type"] = "ExecutionError"
        artifacts["error_message"] = str(e)
        return EvaluationResult(metrics=metrics, artifacts=artifacts)
    if not hasattr(mod, target_fn_name):
        artifacts["error_type"] = "ContractError"
        artifacts["error_message"] = f"Missing required function: {target_fn_name}"
        return EvaluationResult(metrics=metrics, artifacts=artifacts)
    target_fn = getattr(mod, target_fn_name)
    preds = []
    for row in train_data.features:
        try:
            val = float(target_fn(float(row[0]), float(row[1]), float(row[2])))
            if not np.isfinite(val) or val < -1e-7:
                artifacts["error_type"] = "BoundednessError"
                artifacts["error_message"] = f"Output out of bounds or non-finite: {val}"
                return EvaluationResult(metrics=metrics, artifacts=artifacts)
            preds.append(val)
        except Exception as e:
            artifacts["error_type"] = "RuntimeError"
            artifacts["error_message"] = str(e)
            return EvaluationResult(metrics=metrics, artifacts=artifacts)
    preds_arr = np.array(preds, dtype=float)
    tau = kendall_tau_score(preds_arr, train_data.utilities)
    violations = 0
    total = len(train_data.features) * 3
    for metric_idx in range(3):
        for row in train_data.features:
            base_val = target_fn(float(row[0]), float(row[1]), float(row[2]))
            p_row = row.copy()
            p_row[metric_idx] = min(1.0, p_row[metric_idx] + 0.05)
            changed_val = target_fn(float(p_row[0]), float(p_row[1]), float(p_row[2]))
            if (changed_val + 1e-7) < base_val:
                violations += 1
    v_rate = float(violations / max(1, total))
    score = tau - (0.5 * v_rate)
    metrics["combined_score"] = float(score)
    metrics["kendall_tau"] = float(tau)
    metrics["violation_rate"] = float(v_rate)
    return EvaluationResult(metrics=metrics, artifacts=artifacts)
