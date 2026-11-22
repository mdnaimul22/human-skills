from __future__ import annotations
import importlib
from typing import TypeVar
from src.db.helpers.registry import SYSTEM_BRANCH, discover_branches

T = TypeVar("T")

def resolve_domain_symbol(name: str, domain_root: str = "src/db/domain") -> T:
    for branch in discover_branches(domain_root):
        if branch.name == SYSTEM_BRANCH:
            continue
        pkg = importlib.import_module(branch.package)
        if name in pkg.__dict__:
            res: T = pkg.__dict__[name]
            return res
        models_mod = importlib.import_module(f"{branch.package}.models")
        if name in models_mod.__dict__:
            model_res: T = models_mod.__dict__[name]
            return model_res
    raise AttributeError(f"module 'src.db.domain' has no attribute '{name}'")

def __getattr__(name: str) -> T:
    return resolve_domain_symbol(name)
