import numpy as np
from core.expression import Expr

class FitnessValidator:
    def __init__(self, tolerance: float = 1e-7):
        self.tolerance = tolerance

    def is_bounded(self, expr: Expr, samples: np.ndarray) -> bool:
        for row in samples:
            try:
                val = expr.evaluate(row)
            except (OverflowError, ZeroDivisionError, ValueError):
                return False
            if not np.isfinite(val):
                return False
            if val < -self.tolerance:
                return False
        return True

    def metric_monotonicity(self, expr: Expr, samples: np.ndarray, metric_index: int, direction: int, delta: float = 0.05) -> float:
        violations = 0
        total = len(samples)
        if total == 0:
            return 0.0
        for row in samples:
            original = expr.evaluate(row)
            perturbed = row.copy()
            perturbed[metric_index] = np.clip(perturbed[metric_index] + delta, 0.0, 1.0)
            changed = expr.evaluate(perturbed)
            if direction > 0 and (changed + self.tolerance) < original:
                violations += 1
            elif direction < 0 and (changed - self.tolerance) > original:
                violations += 1
        return violations / total

    def total_violation_rate(self, expr: Expr, samples: np.ndarray, directions: list[int]) -> float:
        rates = []
        for idx, direction in enumerate(directions):
            rate = self.metric_monotonicity(expr, samples, idx, direction)
            rates.append(rate)
        return float(np.mean(rates)) if rates else 0.0
