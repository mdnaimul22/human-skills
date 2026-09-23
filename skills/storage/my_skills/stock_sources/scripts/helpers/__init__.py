from __future__ import annotations

import importlib
import inspect
import pkgutil

from .base import Candidate, SearchFilters, StockSource

__all__ = [
    "Candidate",
    "SearchFilters",
    "StockSource",
    "all_sources",
    "available_sources",
    "get_source",
    "source_catalog",
    "source_summary",
]


def _is_source_adapter_class(cls: type) -> bool:
    return (
        inspect.isclass(cls)
        and cls.__module__.startswith(f"{__name__}.")
        and cls.__module__ != f"{__name__}.base"
        and isinstance(getattr(cls, "name", None), str)
        and bool(getattr(cls, "name", None))
        and callable(getattr(cls, "is_available", None))
        and callable(getattr(cls, "search", None))
        and callable(getattr(cls, "download", None))
    )


def _source_classes() -> list[type]:
    discovered: dict[str, type] = {}
    for module_info in pkgutil.iter_modules(__path__, f"{__name__}."):
        if module_info.ispkg or module_info.name.endswith(".base"):
            continue
        module = importlib.import_module(module_info.name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if not _is_source_adapter_class(cls):
                continue
            discovered[getattr(cls, "name")] = cls
    return sorted(
        discovered.values(),
        key=lambda cls: (
            int(getattr(cls, "priority", 100)),
            getattr(cls, "display_name", getattr(cls, "name")).lower(),
        ),
    )


def all_sources() -> list[StockSource]:
    return [cls() for cls in _source_classes()]


def available_sources() -> list[StockSource]:
    return [s for s in all_sources() if s.is_available()]


def source_catalog() -> list[dict[str, object]]:
    catalog: list[dict[str, object]] = []
    for source in all_sources():
        cls = source.__class__
        available = bool(source.is_available())
        catalog.append({
            "name": source.name,
            "display_name": getattr(cls, "display_name", source.name),
            "provider": getattr(cls, "provider", source.name),
            "status": "available" if available else "unavailable",
            "supports": getattr(cls, "supports", {}),
        })
    return catalog


def source_summary() -> dict[str, object]:
    catalog = source_catalog()
    available = [entry["name"] for entry in catalog if entry["status"] == "available"]
    unavailable = [entry["name"] for entry in catalog if entry["status"] != "available"]
    return {
        "configured": len(available),
        "total": len(catalog),
        "available_source_names": available,
        "unavailable_source_names": unavailable,
    }


def get_source(name: str) -> StockSource:
    for s in all_sources():
        if s.name == name:
            return s
    raise KeyError(f"No stock source registered with name={name!r}")
