from __future__ import annotations
import importlib
from dataclasses import dataclass
from sqlalchemy import MetaData, Table
from src.config import get_abs_path, is_dir, is_file, list_files
from src.db.helpers.base import Base

SYSTEM_BRANCH = "system"
_SYSTEM_PACKAGE = "src.db.system"
_DOMAIN_PACKAGE = "src.db.domain"
_DOMAIN_ROOT = "src/db/domain"

@dataclass(frozen=True)
class SchemaBranch:
    name: str
    package: str
    migrations_rel: str

    @property
    def migrations_abs(self) -> str:
        return get_abs_path(self.migrations_rel)

def discover_branches(domain_root: str = _DOMAIN_ROOT) -> list[SchemaBranch]:
    branches = [SchemaBranch(SYSTEM_BRANCH, _SYSTEM_PACKAGE, "src/db/system/migrations")]
    if not is_dir(domain_root):
        return branches
    for entry in sorted(list_files(domain_root, "*"), key=lambda e: e.name):
        rel = f"{domain_root}/{entry.name}"
        if entry.name.startswith("_") or not is_dir(rel) or not is_file(f"{rel}/models.py"):
            continue
        branches.append(SchemaBranch(entry.name, f"{_DOMAIN_PACKAGE}.{entry.name}", f"{rel}/migrations"))
    return branches

def load_metadata(domain_root: str = _DOMAIN_ROOT) -> MetaData:
    for branch in discover_branches(domain_root):
        importlib.import_module(f"{branch.package}.models")
    return Base.metadata

def active_tables(domain_root: str = _DOMAIN_ROOT) -> list[Table]:
    branches = discover_branches(domain_root)
    for branch in branches:
        importlib.import_module(f"{branch.package}.models")
    prefixes = tuple(f"{b.package}." for b in branches)
    seen: set[str] = set()
    tables: list[Table] = []
    for mapper in Base.registry.mappers:
        table = mapper.local_table
        if mapper.class_.__module__.startswith(prefixes) and table.name not in seen:
            seen.add(table.name)
            tables.append(table)
    return tables

def system_table_names() -> set[str]:
    importlib.import_module(f"{_SYSTEM_PACKAGE}.models")
    prefix = f"{_SYSTEM_PACKAGE}."
    return {
        mapper.local_table.name for mapper in Base.registry.mappers
        if mapper.class_.__module__.startswith(prefix)
    }

def branch_tables(branch: SchemaBranch) -> set[str]:
    importlib.import_module(f"{branch.package}.models")
    prefix = f"{branch.package}."
    return {
        mapper.local_table.name for mapper in Base.registry.mappers
        if mapper.class_.__module__.startswith(prefix)
    }
