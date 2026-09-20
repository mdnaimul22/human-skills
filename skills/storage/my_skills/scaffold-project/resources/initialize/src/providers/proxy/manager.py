from datetime import datetime, timedelta
import httpx
from src.config import (
    Settings,
    exists,
    read_json,
    setup_logger,
    write_json,
)
from src.helpers import parse_iso, time_now, time_now_iso

logger = setup_logger(Settings.LOG_DIR / "provider.log", name="myproject.providers.proxy")


class ProxyManager:
    def __init__(self):
        self.cache_path = Settings.PROXY_CACHE_PATH
        self.last_update_path = Settings.PROXY_LAST_UPDATE_PATH
        self.api_url = Settings.WEBSHARE_API_URL
        self.token = Settings.WEBSHARE_TOKEN

    def should_update_proxies(self) -> bool:
        if not exists(self.last_update_path):
            return True
        try:
            data = read_json(self.last_update_path)
            last_update_str = data.get("last_update")
            if not last_update_str:
                return True
            last_update = parse_iso(last_update_str)
            current_date = time_now().date()
            last_update_date = last_update.date()
            return current_date > last_update_date
        except Exception:
            return True

    def fetch_webshare_proxies(self) -> list[str]:
        if not self.api_url.startswith("https://proxy.webshare.io/"):
            logger.error("Invalid proxy provider URL")
            return []

        headers: dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"

        try:
            response = httpx.get(
                self.api_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )
            if response.status_code != 200:
                logger.error(f"Webshare API returned status code: {response.status_code}")
                return []

            proxies: list[str] = []
            for line in response.text.strip().splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                parts = stripped.split(":")
                if len(parts) == 4:
                    host, port, username, password = parts
                    proxies.append(f"http://{username}:{password}@{host}:{port}")
            return proxies
        except Exception as e:
            logger.error(f"Failed fetching proxies: {e}")
            return []

    def save_proxies(self, proxies: list[str]) -> bool:
        try:
            payload = {
                "proxies": proxies,
                "count": len(proxies),
                "updated_at": time_now_iso(),
            }
            write_json(self.cache_path, payload)
            logger.info(f"Saved {len(proxies)} proxies to {self.cache_path}")
            return True
        except Exception as e:
            logger.error(f"Failed writing proxies cache: {e}")
            return False

    def get_proxies(self) -> list[str]:
        if not exists(self.cache_path):
            return []
        try:
            data = read_json(self.cache_path)
            proxies = data.get("proxies")
            return [str(item) for item in proxies] if proxies else []
        except Exception as e:
            logger.error(f"Failed reading proxies cache: {e}")
            return []

    def update_last_update_time(self) -> None:
        try:
            data = {
                "last_update": time_now_iso(),
                "proxies_updated": True,
            }
            write_json(self.last_update_path, data)
        except Exception as e:
            logger.error(f"Failed recording timestamp: {e}")

    def auto_update_proxies(self, force: bool = False) -> bool:
        if not force and not self.should_update_proxies():
            logger.info("Proxies are up to date")
            return True

        logger.info("Syncing proxy list")
        proxies = self.fetch_webshare_proxies()
        if not proxies:
            logger.warning("No proxies fetched")
            return False

        success = self.save_proxies(proxies)
        if not success:
            logger.error("Failed saving proxy cache")
            return False

        self.update_last_update_time()
        logger.info(f"Proxy sync completed with {len(proxies)} items")
        return True

    def get_last_update_info(self) -> dict:
        if not exists(self.last_update_path):
            return {"last_update": None, "proxies_updated": False}
        try:
            return read_json(self.last_update_path)
        except Exception:
            return {"last_update": None, "proxies_updated": False}

    def schedule_next_update(self) -> datetime:
        next_update = time_now() + timedelta(days=1)
        return next_update.replace(hour=0, minute=0, second=0, microsecond=0)