from __future__ import annotations
import httpx
from src.config import Settings, setup_logger
from src.helpers import ExternalServiceError, ValidationError
from ..schema import ProxyProviderType

logger = setup_logger(Settings.LOG_DIR / "proxy.log", name="providers.proxy.fetcher")


def parse_webshare_lines(raw_text: str) -> list[str]:
    proxies: list[str] = []
    seen: set[str] = set()
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "://" in stripped:
            url = stripped
        else:
            parts = stripped.split(":")
            if len(parts) != 4:
                continue
            host, port, username, password = parts
            url = f"http://{username}:{password}@{host}:{port}"
        if url not in seen:
            seen.add(url)
            proxies.append(url)
    return proxies


def parse_static_proxies(raw_csv: str) -> list[str]:
    proxies: list[str] = []
    seen: set[str] = set()
    for item in raw_csv.split(","):
        clean = item.strip()
        if not clean or "://" not in clean:
            continue
        if clean not in seen:
            seen.add(clean)
            proxies.append(clean)
    return proxies


class ProxyFetcher:
    @classmethod
    async def fetch_webshare(cls, api_url: str, token: str, timeout: float) -> list[str]:
        clean_url = api_url.strip()
        if not clean_url or not clean_url.startswith("https://proxy.webshare.io/"):
            raise ValidationError("WEBSHARE_API_URL must be a valid https://proxy.webshare.io/ endpoint")
        headers: dict[str, str] = {}
        if token.strip():
            headers["Authorization"] = f"Token {token.strip()}"
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(clean_url, headers=headers)
        except httpx.HTTPError as err:
            raise ExternalServiceError("Webshare", f"Proxy fetch failed: {err}") from err
        if response.status_code != 200:
            raise ExternalServiceError("Webshare", f"Webshare API returned HTTP {response.status_code}")
        return parse_webshare_lines(response.text)

    @classmethod
    async def fetch(cls, provider: ProxyProviderType) -> list[str]:
        if provider == ProxyProviderType.STATIC:
            return parse_static_proxies(Settings.PROXY_STATIC_URLS)
        return await cls.fetch_webshare(
            api_url=Settings.WEBSHARE_API_URL,
            token=Settings.WEBSHARE_TOKEN,
            timeout=Settings.PROXY_REQUEST_TIMEOUT_SEC,
        )
