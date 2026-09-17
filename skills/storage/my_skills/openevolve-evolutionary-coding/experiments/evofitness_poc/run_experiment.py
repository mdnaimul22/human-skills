import os
import sys
import numpy as np

base_dir = os.path.abspath(os.path.dirname(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from benchmark.synthetic import SyntheticBenchmark
from core.expression import Variable, Multiply, Power, ExpNegative, Reciprocal
from evolution.evaluator_engine import EvoFitnessEvaluator
from evolution.engine import GeneticSearchEngine

def run():
    bench = SyntheticBenchmark()
    train_data, test_data = bench.get_benchmarks()
    evaluator = EvoFitnessEvaluator(metric_directions=[1, 1, 1])

    naive_expr = Variable(0)
    score_naive_train = evaluator.evaluate(naive_expr, train_data)
    score_naive_test = evaluator.evaluate(naive_expr, test_data)

    handcrafted_expr = Multiply(Multiply(Variable(0), Variable(1)), Variable(2))
    score_hc_train = evaluator.evaluate(handcrafted_expr, train_data)
    score_hc_test = evaluator.evaluate(handcrafted_expr, test_data)

    engine = GeneticSearchEngine(
        evaluator=evaluator,
        num_vars=3,
        pop_size=50,
        generations=40,
        seed=42
    )
    best_candidate, history = engine.run(train_data)
    evolved_expr = best_candidate.expr

    score_evo_train = evaluator.evaluate(evolved_expr, train_data)
    score_evo_test = evaluator.evaluate(evolved_expr, test_data)

    print("=========================================================================================")
    print("                  EVOFITNESS: PROOF-OF-CONCEPT EXPERIMENTAL RESULTS                      ")
    print("=========================================================================================")
    print(f"{'Approach':<28} | {'Train τ':<9} | {'Test τ':<9} | {'Violations':<11} | {'Complexity':<10} | {'Gen Gap':<8}")
    print("-" * 89)

    gap_naive = abs(score_naive_train.kendall_tau - score_naive_test.kendall_tau)
    print(
        f"{'Naive (Single-Obj x0)':<28} | "
        f"{score_naive_train.kendall_tau:<9.4f} | "
        f"{score_naive_test.kendall_tau:<9.4f} | "
        f"{score_naive_test.violation_rate:<11.2%} | "
        f"{score_naive_test.complexity:<10} | "
        f"{gap_naive:<8.4f}"
    )

    gap_hc = abs(score_hc_train.kendall_tau - score_hc_test.kendall_tau)
    print(
        f"{'Handcrafted (x0 * x1 * x2)':<28} | "
        f"{score_hc_train.kendall_tau:<9.4f} | "
        f"{score_hc_test.kendall_tau:<9.4f} | "
        f"{score_hc_test.violation_rate:<11.2%} | "
        f"{score_hc_test.complexity:<10} | "
        f"{gap_hc:<8.4f}"
    )

    gap_evo = abs(score_evo_train.kendall_tau - score_evo_test.kendall_tau)
    print(
        f"{'EvoFitness (Discovered F*)':<28} | "
        f"{score_evo_train.kendall_tau:<9.4f} | "
        f"{score_evo_test.kendall_tau:<9.4f} | "
        f"{score_evo_test.violation_rate:<11.2%} | "
        f"{score_evo_test.complexity:<10} | "
        f"{gap_evo:<8.4f}"
    )
    print("=" * 89)
    print(f"Discovered Fitness Expression: F*(X) = {evolved_expr.to_string()}")
    print("Hidden Ground Truth Oracle   : V(X)  = (x0^2) * exp(2*x1 - 2) * ((1 + x2)/2)")
    print("=" * 89)

    success = (
        score_evo_test.kendall_tau > score_naive_test.kendall_tau
        and score_evo_test.violation_rate == 0.0
        and gap_evo < 0.05
    )
    if success:
        print("[VERDICT: EMPIRICALLY CONFIRMED]")
        print("Evolved fitness function generalized to unseen programs and achieved high ranking concordance without violations.")
    else:
        print("[VERDICT: NEEDS REFINEMENT]")

if __name__ == "__main__":
    run()
