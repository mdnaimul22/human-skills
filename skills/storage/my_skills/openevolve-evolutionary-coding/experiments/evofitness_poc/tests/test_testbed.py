import os
import sys
import numpy as np
import pytest

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from core.metrics import MetricSpec, MetricSet
from core.expression import Variable, Constant, Multiply, Add, Power, ExpNegative, Reciprocal
from core.constraints import FitnessValidator
from validation.ranking import kendall_tau_score, discordance_rate
from benchmark.synthetic import SyntheticBenchmark
from evolution.evaluator_engine import EvoFitnessEvaluator
from openevolve_adapter.evaluator import evaluate

def test_metric_normalization():
    s1 = MetricSpec(name="acc", direction=1, minimum=0.0, maximum=100.0)
    res1 = s1.normalize(np.array([0.0, 50.0, 100.0]))
    assert np.allclose(res1, [0.0, 0.5, 1.0])

    s2 = MetricSpec(name="latency", direction=-1, minimum=10.0, maximum=110.0)
    res2 = s2.normalize(np.array([10.0, 60.0, 110.0]))
    assert np.allclose(res2, [1.0, 0.5, 0.0])

    mset = MetricSet(specs=(s1, s2))
    raw = {"acc": np.array([50.0]), "latency": np.array([60.0])}
    matrix = mset.normalize(raw)
    assert matrix.shape == (1, 2)
    assert np.allclose(matrix[0], [0.5, 0.5])

def test_expression_ast():
    x = [0.8, 0.5, 0.2]
    v0 = Variable(0)
    v1 = Variable(1)
    assert v0.evaluate(x) == 0.8
    assert v0.complexity() == 1

    prod = Multiply(v0, v1)
    assert np.isclose(prod.evaluate(x), 0.4)
    assert prod.complexity() == 3

    pwr = Power(v0, 2.0)
    assert np.isclose(pwr.evaluate(x), 0.64)

    exp_neg = ExpNegative(v1, 2.0)
    assert np.isclose(exp_neg.evaluate(x), np.exp(-1.0))

    recip = Reciprocal(v1)
    assert np.isclose(recip.evaluate(x), 1.0 / 1.5)

def test_constraints_validator():
    val = FitnessValidator()
    samples = np.array([[0.2, 0.5, 0.5], [0.8, 0.2, 0.1]])

    good_expr = Variable(0)
    assert val.is_bounded(good_expr, samples)
    rate_good = val.metric_monotonicity(good_expr, samples, metric_index=0, direction=1)
    assert rate_good == 0.0

    bad_expr = Multiply(Variable(0), Constant(-1.0))
    rate_bad = val.metric_monotonicity(bad_expr, samples, metric_index=0, direction=1)
    assert rate_bad > 0.0

def test_ranking_kendall_tau():
    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = np.array([10.0, 20.0, 30.0, 40.0])
    c = np.array([40.0, 30.0, 20.0, 10.0])

    assert np.isclose(kendall_tau_score(a, b), 1.0)
    assert np.isclose(kendall_tau_score(a, c), -1.0)
    assert np.isclose(discordance_rate(a, b), 0.0)
    assert np.isclose(discordance_rate(a, c), 1.0)

def test_synthetic_benchmark():
    bench = SyntheticBenchmark()
    train, test = bench.get_benchmarks()
    assert train.features.shape == (60, 3)
    assert len(train.utilities) == 60
    assert test.features.shape == (200, 3)
    assert len(test.utilities) == 200
    assert np.all((train.utilities >= 0.0) & (train.utilities <= 1.0))

def test_evaluator_engine():
    bench = SyntheticBenchmark()
    train, _ = bench.get_benchmarks()
    evaluator = EvoFitnessEvaluator(metric_directions=[1, 1, 1])
    score = evaluator.evaluate(Variable(0), train)
    assert np.isfinite(score.combined_score)
    assert -1.0 <= score.kendall_tau <= 1.0
    assert score.violation_rate == 0.0

def test_openevolve_adapter_evaluator():
    prog_path = os.path.join(base_dir, "openevolve_adapter", "initial_program.py")
    res = evaluate(prog_path)
    assert "combined_score" in res.metrics
    assert res.metrics["combined_score"] > -1.0
    assert res.artifacts["error_type"] is None
