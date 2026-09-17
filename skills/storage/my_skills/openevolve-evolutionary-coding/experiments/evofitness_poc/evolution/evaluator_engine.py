from dataclasses import dataclass
import numpy as np
from core.expression import Expr
from core.constraints import FitnessValidator
from validation.ranking import kendall_tau_score
from benchmark.synthetic import Dataset

@dataclass(frozen=True)
class EvaluationScore:
    combined_score: float
    kendall_tau: float
    violation_rate: float
    complexity: int

class EvoFitnessEvaluator:
    def __init__(self, metric_directions: list[int], lambda_penalty: float = 0.5, mu_complexity: float = 0.005):
        self.metric_directions = metric_directions
        self.lambda_penalty = lambda_penalty
        self.mu_complexity = mu_complexity
        self.validator = FitnessValidator()

    def evaluate(self, expr: Expr, dataset: Dataset) -> EvaluationScore:
        complexity = expr.complexity()
        if not self.validator.is_bounded(expr, dataset.features):
            return EvaluationScore(
                combined_score=-1.0,
                kendall_tau=-1.0,
                violation_rate=1.0,
                complexity=complexity
            )
        try:
            preds = np.array([expr.evaluate(row) for row in dataset.features], dtype=float)
        except (OverflowError, ZeroDivisionError, ValueError):
            return EvaluationScore(
                combined_score=-1.0,
                kendall_tau=-1.0,
                violation_rate=1.0,
                complexity=complexity
            )
        tau = kendall_tau_score(preds, dataset.utilities)
        violations = self.validator.total_violation_rate(expr, dataset.features, self.metric_directions)
        penalty = self.lambda_penalty * violations + self.mu_complexity * complexity
        combined = tau - penalty
        return EvaluationScore(
            combined_score=float(combined),
            kendall_tau=float(tau),
            violation_rate=float(violations),
            complexity=complexity
        )
