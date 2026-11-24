from __future__ import annotations
import pytest
from src.apps.tunnel import TunnelProvider, normalize_provider
from src.apps.tunnel.helpers import normalize_public_url, origin_from_url, origin_key
from src.helpers import ValidationError


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("cloudflared", TunnelProvider.CLOUDFLARED),
        ("cloudflare", TunnelProvider.CLOUDFLARED),
        ("cloudflare-tunnel", TunnelProvider.CLOUDFLARED),
        ("tailscale", TunnelProvider.TAILSCALE),
        ("tailscale_funnel", TunnelProvider.TAILSCALE),
        ("TAILSCALE-FUNNEL", TunnelProvider.TAILSCALE),
    ],
)
def test_normalize_provider_aliases(raw: str, expected: TunnelProvider) -> None:
    assert normalize_provider(raw) == expected


def test_normalize_provider_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        normalize_provider("serveo")


def test_origins_normalization() -> None:
    assert origin_from_url("https://demo.trycloudflare.com/api/v1") == "https://demo.trycloudflare.com"
    assert origin_from_url("https://demo.ts.net:443/health") == "https://demo.ts.net"
    assert origin_from_url("http://127.0.0.1:8000/test") == "http://127.0.0.1:8000"
    assert origin_from_url("not-a-url") is None
    assert origin_key("https://demo.ts.net/foo") == ("https", "demo.ts.net", 443)
    assert normalize_public_url("api.example.com/") == "https://api.example.com"
    assert normalize_public_url("https://api.example.com/") == "https://api.example.com"
