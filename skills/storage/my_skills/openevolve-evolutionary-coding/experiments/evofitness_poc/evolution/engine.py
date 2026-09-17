from dataclasses import dataclass
import copy
import numpy as np
from core.expression import Expr, Variable, Constant, Multiply, Add, Power, ExpNegative, Reciprocal
from evolution.evaluator_engine import EvoFitnessEvaluator, EvaluationScore
from benchmark.synthetic import Dataset

@dataclass
class Candidate:
    expr: Expr
    score: EvaluationScore

class GeneticSearchEngine:
    def __init__(self, evaluator: EvoFitnessEvaluator, num_vars: int = 3, pop_size: int = 40, generations: int = 35, seed: int = 42):
        self.evaluator = evaluator
        self.num_vars = num_vars
        self.pop_size = pop_size
        self.generations = generations
        self.rng = np.random.default_rng(seed)

    def random_leaf(self) -> Expr:
        return Variable(int(self.rng.integers(0, self.num_vars)))

    def random_tree(self, depth: int = 2) -> Expr:
        if depth <= 0:
            return self.random_leaf()
        op = int(self.rng.integers(0, 4))
        if op == 0:
            return Multiply(self.random_tree(depth - 1), self.random_tree(depth - 1))
        elif op == 1:
            exp = float(self.rng.choice([0.5, 1.0, 1.5, 2.0, 2.5]))
            return Power(self.random_tree(depth - 1), exp)
        elif op == 2:
            scale = float(self.rng.choice([0.5, 1.0, 1.5, 2.0]))
            return ExpNegative(self.random_tree(depth - 1), scale)
        else:
            return Reciprocal(self.random_tree(depth - 1))

    def mutate(self, expr: Expr) -> Expr:
        if expr.complexity() > 18:
            return self.random_leaf()
        dice = float(self.rng.random())
        if dice < 0.25:
            return self.random_tree(depth=1)
        elif dice < 0.50:
            exp = float(self.rng.choice([0.5, 1.0, 1.5, 2.0, 3.0]))
            return Power(expr, exp)
        elif dice < 0.75:
            scale = float(self.rng.choice([0.5, 1.0, 1.5, 2.0]))
            return ExpNegative(expr, scale)
        else:
            leaf = self.random_leaf()
            return Multiply(expr, leaf)

    def seed_population(self, train_data: Dataset) -> list[Candidate]:
        pop = []
        seeds = [
            Variable(0),
            Multiply(Variable(0), Variable(1)),
            Multiply(Power(Variable(0), 2.0), Variable(1)),
            Multiply(Variable(0), ExpNegative(Variable(1))),
        ]
        for s in seeds:
            score = self.evaluator.evaluate(s, train_data)
            pop.append(Candidate(expr=s, score=score))
        while len(pop) < self.pop_size:
            tree = self.random_tree(depth=int(self.rng.integers(1, 3)))
            score = self.evaluator.evaluate(tree, train_data)
            pop.append(Candidate(expr=tree, score=score))
        return pop

    def run(self, train_data: Dataset) -> tuple[Candidate, list[float]]:
        population = self.seed_population(train_data)
        history = []
        for gen in range(self.generations):
            population.sort(key=lambda c: c.score.combined_score, reverse=True)
            best_score = population[0].score.combined_score
            history.append(best_score)
            elites = population[: max(2, self.pop_size // 5)]
            next_pop = list(elites)
            while len(next_pop) < self.pop_size:
                p1 = self.tournament_select(population)
                mutated_expr = self.mutate(p1.expr)
                score = self.evaluator.evaluate(mutated_expr, train_data)
                next_pop.append(Candidate(expr=mutated_expr, score=score))
            population = next_pop
        population.sort(key=lambda c: c.score.combined_score, reverse=True)
        return population[0], history

    def tournament_select(self, pop: list[Candidate], k: int = 3) -> Candidate:
        indices = self.rng.integers(0, len(pop), size=k)
        selected = [pop[i] for i in indices]
        selected.sort(key=lambda c: c.score.combined_score, reverse=True)
        return selected[0]
