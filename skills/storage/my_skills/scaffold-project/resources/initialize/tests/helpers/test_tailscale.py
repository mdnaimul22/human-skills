from __future__ import annotations

from unittest.mock import patch, AsyncMock
import pytest

from src.config import Settings
from src.helpers.exceptions import ExternalServiceError
from src.helpers import (
    is_tailscale_installed,
    get_tailscale_guidance,
    setup_tailscale_ingress,
)
from src.helpers.tailscale import ensure_tailscale_funnel


def test_is_tailscale_installed_returns_bool():
    assert isinstance(is_tailscale_installed(), bool)


def test_guidance_strings_contain_actionable_commands():
    install_msg = get_tailscale_guidance("install")
    assert "curl -fsSL https://tailscale.com/install.sh" in install_msg

    login_msg = get_tailscale_guidance("login", auth_url="https://auth.tailscale.com/test")
    assert "tailscale login" in login_msg
    assert "https://auth.tailscale.com/test" in login_msg

    daemon_msg = get_tailscale_guidance("daemon")
    assert "sudo systemctl start tailscaled" in daemon_msg

    stopped_msg = get_tailscale_guidance("stopped")
    assert "tailscale up" in stopped_msg

    assert "curl -fsSL https://tailscale.com/install.sh" in get_tailscale_guidance("install_guidance")
    assert get_tailscale_guidance("unknown") == ""



@pytest.mark.asyncio
async def test_setup_tailscale_not_installed_raises():
    with patch("src.helpers.tailscale.is_tailscale_installed", return_value=False):
        with pytest.raises(ExternalServiceError) as exc_info:
            await setup_tailscale_ingress(8000)
        assert "not installed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_setup_tailscale_daemon_stopped_raises():
    with patch("src.helpers.tailscale.is_tailscale_installed", return_value=True), \
         patch("src.helpers.tailscale.get_tailscale_status", new_callable=AsyncMock, return_value={}):
        with pytest.raises(ExternalServiceError) as exc_info:
            await setup_tailscale_ingress(8000)
        assert "not running" in str(exc_info.value)


@pytest.mark.asyncio
async def test_setup_tailscale_connection_stopped_raises():
    mock_status = {"BackendState": "Stopped"}
    with patch("src.helpers.tailscale.is_tailscale_installed", return_value=True), \
         patch("src.helpers.tailscale.get_tailscale_status", new_callable=AsyncMock, return_value=mock_status):
        with pytest.raises(ExternalServiceError) as exc_info:
            await setup_tailscale_ingress(8000)
        assert "tailscale up" in str(exc_info.value)


@pytest.mark.asyncio
async def test_setup_tailscale_needs_login_raises():
    mock_status = {
        "BackendState": "NeedsLogin",
        "AuthURL": "https://login.example.com",
    }
    with patch("src.helpers.tailscale.is_tailscale_installed", return_value=True), \
         patch("src.helpers.tailscale.get_tailscale_status", new_callable=AsyncMock, return_value=mock_status):
        with pytest.raises(ExternalServiceError) as exc_info:
            await setup_tailscale_ingress(8000)
        assert "authentication required" in str(exc_info.value)



@pytest.mark.asyncio
async def test_setup_tailscale_success_injects_public_url():
    mock_status = {
        "BackendState": "Running",
        "Self": {
            "DNSName": "my-server.tail12345.ts.net.",
        },
    }
    with patch("src.helpers.tailscale.is_tailscale_installed", return_value=True), \
         patch("src.helpers.tailscale.get_tailscale_status", new_callable=AsyncMock, return_value=mock_status), \
         patch("src.helpers.tailscale.ensure_tailscale_funnel", new_callable=AsyncMock, return_value=True):
        url = await setup_tailscale_ingress(8000)
        assert url == "https://my-server.tail12345.ts.net"
        assert Settings.PUBLIC_URL == "https://my-server.tail12345.ts.net"
