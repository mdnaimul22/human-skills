from __future__ import annotations
from typing import Optional
from ..helpers import NotifyCallback
from ..schema import TunnelProvider
from .base import BaseTunnelProvider
from .cloudflared import CloudflaredProvider
from .tailscale import TailscaleProvider


def create_provider(
    provider: TunnelProvider,
    target_host: str,
    target_port: int,
    timeout: float,
    notify: Optional[NotifyCallback] = None,
) -> BaseTunnelProvider:
    if provider == TunnelProvider.TAILSCALE:
        return TailscaleProvider(target_host=target_host, target_port=target_port, timeout=timeout, notify=notify)
    return CloudflaredProvider(target_host=target_host, target_port=target_port, timeout=timeout, notify=notify)


__all__ = [
    "BaseTunnelProvider",
    "CloudflaredProvider",
    "TailscaleProvider",
    "create_provider",
]
