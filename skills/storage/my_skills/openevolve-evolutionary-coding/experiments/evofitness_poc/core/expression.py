from dataclasses import dataclass
import math
import numpy as np

class Expr:
    def evaluate(self, x: list[float] | np.ndarray) -> float:
        raise NotImplementedError

    def complexity(self) -> int:
        raise NotImplementedError

    def to_string(self) -> str:
        raise NotImplementedError

@dataclass(frozen=True)
class Variable(Expr):
    index: int

    def evaluate(self, x: list[float] | np.ndarray) -> float:
        return float(x[self.index])

    def complexity(self) -> int:
        return 1

    def to_string(self) -> str:
        return f"x{self.index}"

@dataclass(frozen=True)
class Constant(Expr):
    value: float

    def evaluate(self, x: list[float] | np.ndarray) -> float:
        return float(self.value)

    def complexity(self) -> int:
        return 1

    def to_string(self) -> str:
        return f"{self.value:.2f}"

@dataclass(frozen=True)
class Add(Expr):
    left: Expr
    right: Expr

    def evaluate(self, x: list[float] | np.ndarray) -> float:
        return self.left.evaluate(x) + self.right.evaluate(x)

    def complexity(self) -> int:
        return 1 + self.left.complexity() + self.right.complexity()

    def to_string(self) -> str:
        return f"({self.left.to_string()} + {self.right.to_string()})"

@dataclass(frozen=True)
class Multiply(Expr):
    left: Expr
    right: Expr

    def evaluate(self, x: list[float] | np.ndarray) -> float:
        return self.left.evaluate(x) * self.right.evaluate(x)

    def complexity(self) -> int:
        return 1 + self.left.complexity() + self.right.complexity()

    def to_string(self) -> str:
        return f"({self.left.to_string()} * {self.right.to_string()})"

@dataclass(frozen=True)
class ExpNegative(Expr):
    child: Expr
    scale: float = 1.0

    def evaluate(self, x: list[float] | np.ndarray) -> float:
        val = max(0.0, self.child.evaluate(x))
        return math.exp(-self.scale * val)

    def complexity(self) -> int:
        return 2 + self.child.complexity()

    def to_string(self) -> str:
        return f"exp(-{self.scale:.1f}*{self.child.to_string()})"

@dataclass(frozen=True)
class Power(Expr):
    child: Expr
    exponent: float

    def evaluate(self, x: list[float] | np.ndarray) -> float:
        val = max(0.0, self.child.evaluate(x))
        return float(val ** self.exponent)

    def complexity(self) -> int:
        return 2 + self.child.complexity()

    def to_string(self) -> str:
        return f"({self.child.to_string()}^{self.exponent:.1f})"

@dataclass(frozen=True)
class Reciprocal(Expr):
    child: Expr

    def evaluate(self, x: list[float] | np.ndarray) -> float:
        val = max(0.0, self.child.evaluate(x))
        return 1.0 / (1.0 + val)

    def complexity(self) -> int:
        return 2 + self.child.complexity()

    def to_string(self) -> str:
        return f"(1 / (1 + {self.child.to_string()}))"
