from __future__ import annotations

from unittest.mock import MagicMock, patch
from src.apps.nginx.manager import NginxManager, get_nginx_manager


def test_manager_singleton() -> None:
    m1 = NginxManager()
    m2 = NginxManager()
    m3 = get_nginx_manager()
    assert m1 is m2
    assert m2 is m3


def test_manager_status_and_hash() -> None:
    with patch("src.apps.nginx.helpers.compiler.Compiler.get_hash", return_value="hash123"), patch(
        "src.apps.nginx.helpers.installer.Installer.is_installed", return_value=True
    ), patch("src.apps.nginx.helpers.service.Service.is_running", return_value=True), patch(
        "src.apps.nginx.helpers.compiler.Compiler.has_ssl", return_value=True
    ), patch("src.apps.nginx.helpers.compiler.Compiler.has_modsec", return_value=False):
        assert NginxManager.get_config_hash() == "hash123"
        assert NginxManager.is_installed() is True
        assert NginxManager.is_running() is True
        status = NginxManager.get_status()
        assert status.installed is True
        assert status.running is True
        assert status.ssl_enabled is True
        assert status.modsec_enabled is False
        assert status.config_hash == "hash123"


def test_setup_and_reload_skips_when_hash_matches_and_files_exist() -> None:
    state_mock = {
        "backend_domain": "api.example.com",
        "frontend_domain": "example.com",
        "config_hash": "match_hash",
        "deployed_files": [],
    }
    with patch.object(NginxManager, "get_config_hash", return_value="match_hash"), patch(
        "src.apps.nginx.manager.exists", return_value=True
    ), patch("src.apps.nginx.manager.sys_exists", return_value=True), patch(
        "src.apps.nginx.manager.read_json", return_value=state_mock
    ), patch(
        "src.apps.nginx.helpers.service.Service.start_health_probe"
    ) as mock_probe:
        assert NginxManager.setup_and_reload() is True
        assert mock_probe.call_count == 1


def test_setup_and_reload_cleans_old_domain() -> None:
    state_mock = {
        "backend_domain": "old.example.com",
        "frontend_domain": "example.com",
        "config_hash": "old_hash",
        "deployed_files": [],
    }
    with patch.object(NginxManager, "get_config_hash", return_value="new_hash"), patch(
        "src.apps.nginx.manager.exists", side_effect=lambda p: p == "data/apps/nginx/state.json"
    ), patch("src.apps.nginx.manager.read_json", return_value=state_mock), patch(
        "src.apps.nginx.helpers.deployer.Deployer.clean_old"
    ) as mock_clean, patch(
        "src.apps.nginx.helpers.installer.Installer.ensure_installed", return_value=True
    ), patch(
        "src.apps.nginx.helpers.installer.Installer.ensure_dirs", return_value=True
    ), patch(
        "src.apps.nginx.helpers.compiler.Compiler.compile", return_value=True
    ), patch(
        "src.apps.nginx.helpers.deployer.Deployer.deploy", return_value=True
    ), patch(
        "src.apps.nginx.helpers.service.Service.test_and_reload", return_value=True
    ), patch(
        "src.apps.nginx.manager.write_json"
    ) as mock_write, patch(
        "src.apps.nginx.helpers.service.Service.start_health_probe"
    ):
        assert NginxManager.setup_and_reload() is True
        assert mock_clean.call_count == 1
        assert mock_write.call_count == 1


def test_setup_and_reload_fails_on_installer_installed() -> None:
    with patch.object(NginxManager, "get_config_hash", return_value="new_hash"), patch(
        "src.apps.nginx.manager.exists", return_value=False
    ), patch("src.apps.nginx.helpers.installer.Installer.ensure_installed", return_value=False):
        assert NginxManager.setup_and_reload() is False


def test_setup_and_reload_fails_on_installer_dirs() -> None:
    with patch.object(NginxManager, "get_config_hash", return_value="new_hash"), patch(
        "src.apps.nginx.manager.exists", return_value=False
    ), patch("src.apps.nginx.helpers.installer.Installer.ensure_installed", return_value=True), patch(
        "src.apps.nginx.helpers.installer.Installer.ensure_dirs", return_value=False
    ):
        assert NginxManager.setup_and_reload() is False


def test_setup_and_reload_fails_on_compiler() -> None:
    with patch.object(NginxManager, "get_config_hash", return_value="new_hash"), patch(
        "src.apps.nginx.manager.exists", return_value=False
    ), patch("src.apps.nginx.helpers.installer.Installer.ensure_installed", return_value=True), patch(
        "src.apps.nginx.helpers.installer.Installer.ensure_dirs", return_value=True
    ), patch("src.apps.nginx.helpers.compiler.Compiler.compile", return_value=False):
        assert NginxManager.setup_and_reload() is False


def test_setup_and_reload_fails_on_deployer() -> None:
    with patch.object(NginxManager, "get_config_hash", return_value="new_hash"), patch(
        "src.apps.nginx.manager.exists", return_value=False
    ), patch("src.apps.nginx.helpers.installer.Installer.ensure_installed", return_value=True), patch(
        "src.apps.nginx.helpers.installer.Installer.ensure_dirs", return_value=True
    ), patch("src.apps.nginx.helpers.compiler.Compiler.compile", return_value=True), patch(
        "src.apps.nginx.helpers.deployer.Deployer.deploy", return_value=False
    ):
        assert NginxManager.setup_and_reload() is False


def test_setup_and_reload_fails_on_service() -> None:
    with patch.object(NginxManager, "get_config_hash", return_value="new_hash"), patch(
        "src.apps.nginx.manager.exists", return_value=False
    ), patch("src.apps.nginx.helpers.installer.Installer.ensure_installed", return_value=True), patch(
        "src.apps.nginx.helpers.installer.Installer.ensure_dirs", return_value=True
    ), patch("src.apps.nginx.helpers.compiler.Compiler.compile", return_value=True), patch(
        "src.apps.nginx.helpers.deployer.Deployer.deploy", return_value=True
    ), patch("src.apps.nginx.helpers.service.Service.test_and_reload", return_value=False):
        assert NginxManager.setup_and_reload() is False


def test_reload_delegation() -> None:
    with patch("src.apps.nginx.helpers.compiler.Compiler.compile", return_value=True), patch(
        "src.apps.nginx.helpers.deployer.Deployer.deploy", return_value=True
    ), patch("src.apps.nginx.helpers.service.Service.test_and_reload", return_value=True):
        assert NginxManager.reload() is True

    with patch("src.apps.nginx.helpers.compiler.Compiler.compile", return_value=False):
        assert NginxManager.reload() is False


def test_backward_compatible_aliases() -> None:
    assert callable(NginxManager.compile_configs)
    assert callable(NginxManager.deploy_configs)
    assert callable(NginxManager.test_and_reload)
    assert callable(NginxManager.ensure_nginx_installed)
    assert callable(NginxManager.ensure_system_directories)
    assert callable(NginxManager.cleanup_old_configs)
