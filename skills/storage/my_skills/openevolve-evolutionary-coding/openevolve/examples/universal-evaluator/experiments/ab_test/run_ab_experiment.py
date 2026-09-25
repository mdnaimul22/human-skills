import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from evaluator.bridge import OpenEvolveBridge
from legacy_evaluator import LegacyEvaluator


def run_experiment():
    os.environ.setdefault("LAYA_API_KEY", "sk-9405ffec0936cb65-c598e2-30b6f2b0")
    os.environ.setdefault("LAYA_MODEL", "typed-decisions")
    os.environ.setdefault("LAYA_ENDPOINT", "https://momen-gpu.tail374b2b.ts.net:8020/predict")

    base_dir = Path(__file__).resolve().parent
    spec_path = base_dir / "spec.json"
    candidates_dir = base_dir / "candidates"
    tests_dir = base_dir / "tests"

    legacy = LegacyEvaluator()
    bridge = OpenEvolveBridge(
        spec=spec_path,
        support_map={"tests": "tests"},
        entrypoint="main.py",
    )
    bridge.project_root = base_dir

    candidate_files = [
        ("C1: Optimal (Timsort)", candidates_dir / "c1_optimal.py", "100% correct, O(N log N) optimal"),
        ("C2: Inefficient (Bubble)", candidates_dir / "c2_slow.py", "Correct output, O(N^2) slow"),
        ("C3: Buggy (Set Dedupe)", candidates_dir / "c3_buggy.py", "Fails empty list & duplicate preservation"),
        ("C4: Syntax Error", candidates_dir / "c4_syntax_error.py", "Uncompilable code (broken signature)"),
        ("C5: Adversarial / Cheat", candidates_dir / "c5_adversarial.py", "Hardcoded fake return [1,2,3] + fs touch"),
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
                "valid": leg_res.get("valid", False),
                "time_ms": leg_time_ms,
                "error": leg_res.get("artifacts", {}).get("error", ""),
            },
            "universal": {
                "fitness": ue_res.metrics.get("combined_score", 0.0),
                "valid": bool(ue_res.metrics.get("valid", 0.0)),
                "test_pass_rate": ue_res.metrics.get("test_pass_rate", 0.0),
                "sorting_efficiency": ue_res.metrics.get("sorting_efficiency", 0.0),
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
