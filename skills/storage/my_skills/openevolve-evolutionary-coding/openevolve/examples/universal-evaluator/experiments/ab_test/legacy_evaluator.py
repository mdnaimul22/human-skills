import importlib.util
from pathlib import Path
import time
from typing import Any


class LegacyEvaluator:
    def evaluate(self, program_path: str | Path) -> dict[str, Any]:
        path = Path(program_path).resolve()
        start = time.perf_counter()
        try:
            spec = importlib.util.spec_from_file_location("candidate_mod", str(path))
            if spec is None or spec.loader is None:
                return {
                    "combined_score": 0.0,
                    "valid": False,
                    "metrics": {"pass_rate": 0.0, "time_ms": 0.0},
                    "artifacts": {"error": "Failed to load module spec"},
                }
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "sort_numbers"):
                return {
                    "combined_score": 0.0,
                    "valid": False,
                    "metrics": {"pass_rate": 0.0, "time_ms": 0.0},
                    "artifacts": {"error": "Missing required function sort_numbers"},
                }

            func = getattr(module, "sort_numbers")
            test_cases = [
                ([3, 1, 2], [1, 2, 3]),
                ([2, 1, 2, 1], [1, 1, 2, 2]),
                ([], []),
                ([3, -1, 0, -5], [-5, -1, 0, 3]),
                (list(range(500, 0, -1)), list(range(1, 501))),
            ]

            passed = 0
            for inp, exp in test_cases:
                try:
                    res = func(list(inp))
                    if res == exp:
                        passed += 1
                except Exception:
                    pass

            elapsed_ms = (time.perf_counter() - start) * 1000
            pass_rate = passed / len(test_cases)
            time_factor = 1.0 / (1.0 + (elapsed_ms / 100.0))
            score = (pass_rate * 0.7) + (time_factor * 0.3)

            return {
                "combined_score": score,
                "valid": True,
                "metrics": {
                    "pass_rate": pass_rate,
                    "time_ms": elapsed_ms,
                    "score": score,
                },
                "artifacts": {
                    "passed_cases": f"{passed}/{len(test_cases)}",
                },
            }
        except Exception as exc:
            return {
                "combined_score": 0.0,
                "valid": False,
                "metrics": {"pass_rate": 0.0, "time_ms": 0.0},
                "artifacts": {"error": str(exc)},
            }
