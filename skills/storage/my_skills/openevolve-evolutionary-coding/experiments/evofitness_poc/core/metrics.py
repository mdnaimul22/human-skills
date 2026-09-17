from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class MetricSpec:
    name: str
    direction: int
    minimum: float
    maximum: float

    def normalize(self, values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=float)
        span = self.maximum - self.minimum
        if span <= 0:
            raise ValueError(f"Invalid metric range: {self.name}")
        scaled = np.clip((arr - self.minimum) / span, 0.0, 1.0)
        if self.direction < 0:
            scaled = 1.0 - scaled
        return scaled

@dataclass(frozen=True)
class MetricSet:
    specs: tuple[MetricSpec, ...]

    def normalize(self, raw: dict[str, np.ndarray]) -> np.ndarray:
        cols = []
        for spec in self.specs:
            if spec.name not in raw:
                raise KeyError(f"Metric not found: {spec.name}")
            cols.append(spec.normalize(raw[spec.name]))
        return np.column_stack(cols)
