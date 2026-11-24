from __future__ import annotations

from unittest.mock import patch
import pytest
from src.config import Settings, read_text
from src.apps.nginx.helpers.compiler import Compiler


@pytest.fixture(autouse=True)
def _pin_nginx_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Settings, "BACKEND_DOMAIN", "api.example.com")
    monkeypatch.setattr(Settings, "FRONTEND_DOMAIN", "example.com")
    monkeypatch.setattr(Settings, "NGINX_ENABLE_HTTP2", False)


def test_get_hash_deterministic() -> None:
    h1 = Compiler.get_hash()
    h2 = Compiler.get_hash()
    assert len(h1) == 64
    assert h1 == h2


def test_has_modsec() -> None:
    with patch("src.apps.nginx.helpers.compiler.sys_exists", return_value=True):
        assert Compiler.has_modsec() is True
    with patch("src.apps.nginx.helpers.compiler.sys_exists", return_value=False):
        assert Compiler.has_modsec() is False


def test_has_ssl() -> None:
    with patch("src.apps.nginx.helpers.compiler.sys_exists", side_effect=[True, True]):
        assert Compiler.has_ssl("api.example.com") is True
    with patch("src.apps.nginx.helpers.compiler.sys_exists", return_value=False):
        assert Compiler.has_ssl("api.example.com") is False


def test_build_backend_site_no_ssl() -> None:
    conf = Compiler.build_backend_site(has_ssl=False, has_modsec=False)
    assert "listen 80;" in conf
    assert ":443 ssl;" not in conf
    assert "modsecurity on;" not in conf
    assert "keepalive 64;" in conf
    assert "proxy_http_version 1.1;" in conf
    assert "upstream backend_servers_api_example_com {" in conf
    assert "zone=api_limit_zone_api_example_com:" in conf
    assert "proxy_pass http://backend_servers_api_example_com;" in conf


def test_build_backend_site_scopes_upstream_and_zone_per_domain() -> None:
    with patch("src.apps.nginx.helpers.compiler.Settings.BACKEND_DOMAIN", "127.0.0.1"):
        conf = Compiler.build_backend_site(has_ssl=False, has_modsec=False)
    assert "upstream backend_servers_127_0_0_1 {" in conf
    assert "zone=api_limit_zone_127_0_0_1:" in conf
    assert "proxy_pass http://backend_servers_127_0_0_1/health;" in conf
    assert "upstream backend_servers {" not in conf


def test_build_backend_site_with_ssl_and_modsec() -> None:
    conf = Compiler.build_backend_site(has_ssl=True, has_modsec=True)
    assert ":443 ssl;" in conf
    assert ":443 ssl http2;" not in conf
    assert "modsecurity on;" in conf
    assert "return 301 https://" in conf
    assert "keepalive 64;" in conf


def test_build_frontend_site() -> None:
    conf = Compiler.build_frontend_site(has_ssl=True, has_modsec=False)
    assert ":443 ssl;" in conf
    assert ":443 ssl http2;" not in conf
    assert "proxy_pass http://127.0.0.1:3000;" in conf
    assert "proxy_http_version 1.1;" in conf


def test_build_ssl_listen_part_toggle_http2() -> None:
    with patch("src.apps.nginx.helpers.compiler.Settings.NGINX_ENABLE_HTTP2", True):
        part = Compiler.build_ssl_listen_part()
        assert ":443 ssl http2;" in part
    with patch("src.apps.nginx.helpers.compiler.Settings.NGINX_ENABLE_HTTP2", False):
        part = Compiler.build_ssl_listen_part()
        assert ":443 ssl;" in part
        assert "http2" not in part


def test_compile_success() -> None:
    with patch.object(Compiler, "has_ssl", return_value=False), patch.object(
        Compiler, "has_modsec", return_value=False
    ):
        assert Compiler.compile() is True
        backend_conf = read_text("data/apps/nginx/api.example.com")
        assert "listen 80;" in backend_conf
        bot_conf = read_text("data/apps/nginx/bot_block.conf")
        assert "deny all;" in bot_conf


def test_compile_exception() -> None:
    with patch("src.apps.nginx.helpers.compiler.write_text", side_effect=IOError("disk full")):
        assert Compiler.compile() is False
