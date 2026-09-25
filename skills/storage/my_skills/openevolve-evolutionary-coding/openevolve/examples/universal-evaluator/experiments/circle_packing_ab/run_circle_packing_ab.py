import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from evaluator.bridge import OpenEvolveBridge
from evaluator.metrics.registry import MetricRegistry
from evaluator.metrics.circle_packing import CirclePackingMetricProvider
from legacy_evaluator import LegacyCirclePackingEvaluator


def run_experiment():
    os.environ.setdefault("LAYA_API_KEY", "sk-9405ffec0936cb65-c598e2-30b6f2b0")
    os.environ.setdefault("LAYA_MODEL", "typed-decisions")
    os.environ.setdefault("LAYA_ENDPOINT", "https://momen-gpu.tail374b2b.ts.net:8020/predict")

    base_dir = Path(__file__).resolve().parent
    spec_path = base_dir / "spec.json"
    candidates_dir = base_dir / "candidates"

    metric_registry = MetricRegistry.canonical()
    metric_registry.register(CirclePackingMetricProvider())

    legacy = LegacyCirclePackingEvaluator()
    bridge = OpenEvolveBridge(
        spec=spec_path,
        entrypoint="main.py",
        metric_registry=metric_registry,
    )
    bridge.project_root = base_dir

    candidate_files = [
        ("C1: Optimal Packing", candidates_dir / "c1_optimal.py", "26 disjoint circles strictly inside [0,1]^2 (sum_radii=1.54, valid=True)"),
        ("C2: Suboptimal Packing", candidates_dir / "c2_suboptimal.py", "26 disjoint circles, small radii (sum_radii=0.31, valid=True)"),
        ("C3: Overlapping Cheat", candidates_dir / "c3_overlapping_cheat.py", "26 concentric overlapping circles (fake sum_radii=3.90)"),
        ("C4: Boundary Escape", candidates_dir / "c4_boundary_escape.py", "26 circles placed outside unit square (coord 1.5, fake sum_radii=2.60)"),
        ("C5: Syntax Error", candidates_dir / "c5_syntax_error.py", "Broken syntax (unclosed function header)"),
    ]

    results = []

    for name, path, description in candidate_files:
        t0 = time.perf_counter()
        leg_res = legacy.evaluate(path)
        leg_time_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        s1_res = bridge.evaluate_stage1(path)
        s1_time_ms = (time.perf_counter() - t1) * 1000

        if s1_res.metrics.get("valid", 0.0) == 1.0:
            t2 = time.perf_counter()
            ue_res = bridge.evaluate(path)
            ue_time_ms = s1_time_ms + ((time.perf_counter() - t2) * 1000)
            stage1_passed = True
        else:
            ue_res = s1_res
            ue_time_ms = s1_time_ms
            stage1_passed = False

        judge_arts = {k: v for k, v in ue_res.artifacts.items() if k.startswith("judge_")}

        results.append({
            "name": name,
            "description": description,
            "legacy": {
                "score": leg_res.get("combined_score", 0.0),
                "valid": bool(leg_res.get("validity", 0.0) == 1.0),
                "sum_radii": leg_res.get("sum_radii", 0.0),
                "target_ratio": leg_res.get("target_ratio", 0.0),
                "time_ms": leg_time_ms,
            },
            "universal": {
                "fitness": ue_res.metrics.get("combined_score", 0.0),
                "valid": bool(ue_res.metrics.get("valid", 0.0)),
                "valid_packing": ue_res.metrics.get("valid_packing", 0.0),
                "circle_sum_radii": ue_res.metrics.get("circle_sum_radii", 0.0),
                "packing_density": ue_res.metrics.get("packing_density", 0.0),
                "geometric_rigor": ue_res.metrics.get("geometric_rigor", 0.0),
                "runtime_ms": ue_res.metrics.get("runtime_ms", 0.0),
                "judgments": judge_arts,
                "stage1_passed": stage1_passed,
                "time_ms": ue_time_ms,
                "failures": ue_res.artifacts.get("failure_reasons", ""),
                "suggestion": ue_res.artifacts.get("suggestion", ""),
            },
        })

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run_experiment()
