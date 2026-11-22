from __future__ import annotations
import importlib
from typing import TypeVar

T = TypeVar("T")

_MANAGERS: dict[str, str] = {
    "AuthManager": ".auth",
    "get_auth_manager": ".auth",
    "CertbotManager": ".certbot",
    "get_certbot_manager": ".certbot",
    "DockerManager": ".docker",
    "get_docker_manager": ".docker",
    "GitManager": ".git",
    "get_git_manager": ".git",
    "JobManager": ".jobs",
    "get_manager": ".jobs",
    "NginxManager": ".nginx",
    "get_nginx_manager": ".nginx",
    "SystemManager": ".system",
    "get_system_manager": ".system",
    "WAFManager": ".waf",
}

__all__ = list(_MANAGERS.keys())


def __getattr__(name: str) -> T:
    mod_path = _MANAGERS.get(name)
    if mod_path is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    module = importlib.import_module(mod_path, __name__)
    try:
        val: T = module.__dict__[name]
    except KeyError:
        val = module.__getattr__(name)
    globals()[name] = val
    return val
