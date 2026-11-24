from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from ..helpers import NotifyCallback
from ..schema import TunnelEventType, TunnelProvider


class BaseTunnelProvider(ABC):
    provider: TunnelProvider

    def __init__(
        self,
        target_host: str,
        target_port: int,
        timeout: float = 45.0,
        notify: Optional[NotifyCallback] = None,
    ) -> None:
        self.target_host = target_host
        self.target_port = target_port
        self.timeout = timeout
        self._notify = notify
        self.tunnel_url: Optional[str] = None

    def emit(self, event: TunnelEventType, message: str, url: Optional[str] = None) -> None:
        if self._notify is not None:
            self._notify(event, message, url)

    @abstractmethod
    def start(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_alive(self) -> bool:
        raise NotImplementedError
