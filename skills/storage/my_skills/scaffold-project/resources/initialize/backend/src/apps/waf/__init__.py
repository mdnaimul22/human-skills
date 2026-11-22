from __future__ import annotations
import importlib
from typing import TypeVar

T = TypeVar("T")

_LAZY_EXPORTS: dict[str, str] = {
    "WAFManager": ".manager",
    "ThreatCategory": ".schema",
    "RuleMatch": ".schema",
    "InspectionResult": ".schema",
    "BanRecord": ".schema",
    "RateLimitDecision": ".schema",
    "TrafficEntry": ".schema",
    "WAFStats": ".schema",
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str) -> T:
    mod_path = _LAZY_EXPORTS.get(name)
    if mod_path is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    module = importlib.import_module(mod_path, __name__)
    val: T = module.__dict__[name]
    globals()[name] = val
    return val
