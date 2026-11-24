from __future__ import annotations

from typing import Optional
from src.config import Settings, ensure_dir, exists, read_json, setup_logger, sys_exists, write_json
from src.helpers import get_now_iso
from src.apps.nginx.schema import NGINX_STATE_ADAPTER, NginxState, NginxStatus
from .helpers import (
    Compiler, Deployer, Installer, Service,
)

logger = setup_logger(Settings.LOG_DIR / "nginx.log", name="apps.nginx.manager")

STATE_FILE = "data/apps/nginx/state.json"


class NginxManager:
    _instance: Optional[NginxManager] = None

    def __new__(cls) -> NginxManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_config_hash(cls) -> str:
        return Compiler.get_hash()

    @classmethod
    def is_installed(cls) -> bool:
        return Installer.is_installed()

    @classmethod
    def is_running(cls) -> bool:
        return Service.is_running()

    @classmethod
    def get_status(cls) -> NginxStatus:
        return NginxStatus(
            installed=Installer.is_installed(),
            running=Service.is_running(),
            backend_domain=Settings.BACKEND_DOMAIN,
            frontend_domain=Settings.FRONTEND_DOMAIN,
            ssl_enabled=Compiler.has_ssl(Settings.BACKEND_DOMAIN),
            modsec_enabled=Compiler.has_modsec(),
            config_hash=Compiler.get_hash(),
        )

    @classmethod
    def _get_expected_files(cls) -> list[str]:
        return [
            f"/etc/nginx/sites-available/{Settings.BACKEND_DOMAIN}",
            f"/etc/nginx/sites-available/{Settings.FRONTEND_DOMAIN}",
            "/etc/nginx/snippets/bot_block.conf",
            f"/etc/nginx/sites-enabled/{Settings.BACKEND_DOMAIN}",
            f"/etc/nginx/sites-enabled/{Settings.FRONTEND_DOMAIN}",
        ]

    @classmethod
    def _read_previous_state(cls) -> tuple[Optional[str], Optional[str], Optional[str]]:
        if not exists(STATE_FILE):
            return None, None, None
        try:
            state = NGINX_STATE_ADAPTER.validate_python(read_json(STATE_FILE))
            return state.backend_domain, state.frontend_domain, state.config_hash
        except Exception as e:
            logger.warning(f"Failed to read or validate Nginx state file: {e}")
            return None, None, None

    @classmethod
    def _should_skip_reload(cls, old_hash: Optional[str], current_hash: str) -> bool:
        if old_hash != current_hash:
            return False
        return all(sys_exists(f) for f in cls._get_expected_files())

    @classmethod
    def _sync_old_domains(cls, old_backend: Optional[str], old_frontend: Optional[str]) -> None:
        if old_backend and old_backend != Settings.BACKEND_DOMAIN:
            Deployer.clean_old(old_backend, old_frontend or "")
        elif old_frontend and old_frontend != Settings.FRONTEND_DOMAIN:
            Deployer.clean_old(old_backend or "", old_frontend)

    @classmethod
    def _execute_pipeline(cls) -> bool:
        if not Installer.ensure_installed():
            logger.error("Nginx installation verification failed.")
            return False
        if not Installer.ensure_dirs():
            logger.error("Nginx system directories verification failed.")
            return False
        if not Compiler.compile():
            logger.error("Nginx configuration compilation failed.")
            return False
        if not Deployer.deploy():
            logger.error("Nginx configuration deployment failed.")
            return False
        if not Service.test_and_reload():
            logger.error("Nginx configuration verification or reload failed.")
            return False
        return True

    @classmethod
    def _persist_state(cls, current_hash: str) -> None:
        try:
            ensure_dir("data/apps/nginx")
            new_state = NginxState(
                backend_domain=Settings.BACKEND_DOMAIN,
                frontend_domain=Settings.FRONTEND_DOMAIN,
                config_hash=current_hash,
                deployed_files=cls._get_expected_files(),
                last_reloaded_at=get_now_iso(),
            )
            write_json(STATE_FILE, new_state.model_dump())
            logger.info("Successfully updated Nginx state file.")
        except Exception as e:
            logger.warning(f"Failed to save Nginx state: {e}")

    @classmethod
    def setup_and_reload(cls) -> bool:
        logger.info("Initializing dynamic NginxManager setup flow...")
        current_hash = cls.get_config_hash()
        old_backend, old_frontend, old_hash = cls._read_previous_state()

        if cls._should_skip_reload(old_hash, current_hash):
            logger.info("Nginx configuration hash matches and files exist on system. Skipping deployment and reload.")
            Service.start_health_probe()
            return True

        cls._sync_old_domains(old_backend, old_frontend)

        if not cls._execute_pipeline():
            return False

        cls._persist_state(current_hash)
        Service.start_health_probe()
        return True

    @classmethod
    def reload(cls) -> bool:
        if not Compiler.compile():
            return False
        if not Deployer.deploy():
            return False
        return Service.test_and_reload()

    compile_configs = Compiler.compile
    deploy_configs = Deployer.deploy
    test_and_reload = Service.test_and_reload
    ensure_nginx_installed = Installer.ensure_installed
    ensure_system_directories = Installer.ensure_dirs
    cleanup_old_configs = Deployer.clean_old


def get_nginx_manager() -> NginxManager:
    return NginxManager()
