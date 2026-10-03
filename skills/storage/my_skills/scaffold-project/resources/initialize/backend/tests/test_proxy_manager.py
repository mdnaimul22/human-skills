from src.config import Settings, exists, delete
from src.providers.proxy.manager import ProxyManager


def test_proxy_manager_initialization():
    pm = ProxyManager()
    assert pm.cache_path == Settings.PROXY_CACHE_PATH
    assert pm.last_update_path == Settings.PROXY_LAST_UPDATE_PATH
    assert pm.api_url == Settings.WEBSHARE_API_URL


def test_proxy_manager_save_and_get_proxies():
    pm = ProxyManager()
    test_proxies = ["https://user:pass@10.0.0.1:8080", "https://user:pass@10.0.0.2:8080"]
    success = pm.save_proxies(test_proxies)
    assert success is True
    assert exists(pm.cache_path)

    loaded = pm.get_proxies()
    assert len(loaded) == 2
    assert loaded[0] == test_proxies[0]
    assert loaded[1] == test_proxies[1]

    delete(pm.cache_path)


def test_proxy_manager_update_time():
    pm = ProxyManager()
    pm.update_last_update_time()
    info = pm.get_last_update_info()
    assert info.get("proxies_updated") is True
    assert info.get("last_update") is not None


def test_proxy_manager_schedule_next_update():
    pm = ProxyManager()
    next_dt = pm.schedule_next_update()
    assert next_dt.hour == 0
    assert next_dt.minute == 0
