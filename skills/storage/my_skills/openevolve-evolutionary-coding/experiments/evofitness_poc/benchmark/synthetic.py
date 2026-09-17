from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Dataset:
    features: np.ndarray
    utilities: np.ndarray

class SyntheticBenchmark:
    def __init__(self):
        self.metric_names = ["correctness", "speed", "memory_efficiency"]
        self.metric_directions = [1, 1, 1]

    @staticmethod
    def oracle_utility(x: np.ndarray) -> float:
        x0, x1, x2 = float(x[0]), float(x[1]), float(x[2])
        u = (x0 ** 2) * np.exp(2.0 * x1 - 2.0) * ((1.0 + x2) / 2.0)
        return float(np.clip(u, 0.0, 1.0))

    def evaluate_population(self, x_matrix: np.ndarray) -> np.ndarray:
        return np.array([self.oracle_utility(row) for row in x_matrix], dtype=float)

    def generate_dataset(self, num_samples: int, seed: int) -> Dataset:
        rng = np.random.default_rng(seed)
        x = rng.uniform(0.05, 1.0, size=(num_samples, 3))
        u = self.evaluate_population(x)
        return Dataset(features=x, utilities=u)

    def get_benchmarks(self) -> tuple[Dataset, Dataset]:
        train = self.generate_dataset(num_samples=60, seed=42)
        test = self.generate_dataset(num_samples=200, seed=1337)
        return train, test
