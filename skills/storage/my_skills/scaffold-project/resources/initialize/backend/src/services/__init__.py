from __future__ import annotations
import importlib
from typing import TypeVar

T = TypeVar("T")

_LAZY_MODULES: dict[str, str] = {
    "apps": ".apps",
    "auth_service": ".apps.auth",
    "auth": ".apps.auth",
    "system_service": ".apps.system",
    "system": ".apps.system",
}

__all__ = list(_LAZY_MODULES.keys())


def __getattr__(name: str) -> T:
    target = _LAZY_MODULES.get(name)
    if target is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    mod: T = importlib.import_module(target, __name__)
    globals()[name] = mod
    return mod
