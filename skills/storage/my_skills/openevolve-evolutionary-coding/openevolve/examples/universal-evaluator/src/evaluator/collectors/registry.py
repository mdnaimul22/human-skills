from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import re
from typing import Any, Type

from pydantic import BaseModel

from evaluator.models.spec import CollectorConfig

from .api import APICollector
from .artifact import ArtifactCollector
from .base import EvidenceCollector
from .benchmark import BenchmarkCollector
from .build import BuildCollector
from .coverage import CoverageCollector
from .dependency import DependencyCollector
from .gpu import GPUCollector
from .resource import ResourceCollector
from .runtime import RuntimeCollector
from .security import SecurityCollector
from .sql import SQLCollector
from .static import StaticCollector
from .test import TestCollector

CollectorFactory = Callable[[], EvidenceCollector]
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class CollectorDescriptor:
    name: str
    version: str
    capabilities: frozenset[str]
    config_type: Type[BaseModel]
    factory: CollectorFactory


class CollectorRegistry:
    """Trusted registry for collector discovery, configuration and capability validation."""

    def __init__(self, descriptors: Iterable[CollectorDescriptor] | None = None):
        self._descriptors: dict[str, CollectorDescriptor] = {}
        for descriptor in descriptors or ():
            self.register(descriptor)

    def register(self, descriptor: CollectorDescriptor) -> None:
        if not descriptor.name.strip():
            raise ValueError("collector name must not be empty")
        if descriptor.name in self._descriptors:
            raise ValueError(f"collector already registered: {descriptor.name}")
        implementation = descriptor.factory()
        if implementation.name != descriptor.name:
            raise ValueError(
                f"collector registry name mismatch: key={descriptor.name!r}, "
                f"implementation={implementation.name!r}"
            )
        if implementation.version != descriptor.version:
            raise ValueError(
                f"collector version mismatch for {descriptor.name}: "
                f"descriptor={descriptor.version}, implementation={implementation.version}"
            )
        self._descriptors[descriptor.name] = descriptor

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._descriptors))

    def descriptor(self, collector_type: str) -> CollectorDescriptor:
        try:
            return self._descriptors[collector_type]
        except KeyError as exc:
            raise ValueError(f"unknown collector type: {collector_type}") from exc

    def create(self, collector_type: str) -> EvidenceCollector:
        return self.descriptor(collector_type).factory()

    def capabilities(self, collector_type: str) -> frozenset[str]:
        return self.descriptor(collector_type).capabilities

    def validate_config(self, config: CollectorConfig) -> None:
        descriptor = self.descriptor(config.type)
        if not isinstance(config, descriptor.config_type):
            raise ValueError(
                f"invalid configuration for collector {config.type}: "
                f"expected {descriptor.config_type.__name__}, got {type(config).__name__}"
            )
        requested = getattr(config, "version", None)
        if requested is not None and not _version_matches(requested, descriptor.version):
            raise ValueError(
                f"collector {config.type} version mismatch: requested {requested}, "
                f"installed {descriptor.version}"
            )
        required = set(getattr(config, "required_capabilities", ()))
        missing = required - descriptor.capabilities
        if missing:
            raise ValueError(
                f"collector {config.type} does not provide required capabilities: "
                f"{sorted(missing)}"
            )

    def validate_configs(self, configs: Iterable[CollectorConfig]) -> None:
        seen_ids: set[str] = set()
        seen_types: set[str] = set()
        for config in configs:
            if config.id in seen_ids:
                raise ValueError(f"duplicate collector id: {config.id}")
            if config.type in seen_types:
                raise ValueError(f"collector type configured more than once: {config.type}")
            seen_ids.add(config.id)
            seen_types.add(config.type)
            self.validate_config(config)

    def resolve(self, configs: Iterable[CollectorConfig]) -> list[EvidenceCollector]:
        configs = list(configs)
        self.validate_configs(configs)
        return [self.create(config.type) for config in configs if config.enabled]

    @classmethod
    def canonical(cls) -> "CollectorRegistry":
        from evaluator.models.spec import (
            APICollectorConfig, ArtifactCollectorConfig, CommandCollectorConfig,
            CoverageCollectorConfig, DependencyCollectorConfig, GPUCollectorConfig,
            ResourceCollectorConfig, SQLCollectorConfig, SecurityCollectorConfig,
        )

        entries = [
            ("build", "0.1.0", {"build", "filesystem"}, CommandCollectorConfig, BuildCollector),
            ("test", "0.1.0", {"correctness", "process"}, CommandCollectorConfig, TestCollector),
            ("runtime", "0.1.0", {"runtime", "process"}, CommandCollectorConfig, RuntimeCollector),
            ("benchmark", "0.1.0", {"benchmark", "process"}, CommandCollectorConfig, BenchmarkCollector),
            ("static", "0.1.0", {"static", "filesystem"}, CommandCollectorConfig, StaticCollector),
            ("sql", "1.0.0", {"sql", "database"}, SQLCollectorConfig, SQLCollector),
            ("security", "1.0.0", {"security", "scanner"}, SecurityCollectorConfig, SecurityCollector),
            ("gpu", "1.0.0", {"gpu", "nvidia-smi"}, GPUCollectorConfig, GPUCollector),
            ("api", "1.0.0", {"http", "api"}, APICollectorConfig, APICollector),
            ("coverage", "1.0.0", {"coverage", "process"}, CoverageCollectorConfig, CoverageCollector),
            ("dependency", "1.0.0", {"dependency", "package-metadata"}, DependencyCollectorConfig, DependencyCollector),
            ("resource", "1.0.0", {"resource", "process"}, ResourceCollectorConfig, ResourceCollector),
            ("artifact", "1.0.0", {"artifact", "filesystem"}, ArtifactCollectorConfig, ArtifactCollector),
        ]
        return cls(
            CollectorDescriptor(name, version, frozenset(capabilities), config_type, factory)
            for name, version, capabilities, config_type, factory in entries
        )


def _version_matches(requested: str, installed: str) -> bool:
    """Support exact versions and simple compatible-major requests (e.g. 1.x)."""
    if requested == installed:
        return True
    if requested.endswith(".x"):
        return requested[:-2] == installed.split(".", 1)[0]
    requested_match = _VERSION_RE.match(requested)
    installed_match = _VERSION_RE.match(installed)
    if requested_match and installed_match:
        return requested_match.group(1) == installed_match.group(1) and int(installed_match.group(2)) <= int(requested_match.group(2))
    return False
