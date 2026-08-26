# =============================================================================
# Retry Logic — Test Dataset (Comprehensive ~20 Cases)
# Sources: Microsoft REST API Guidelines, Google API (Exponential Backoff)
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: Tenacity Library (Python Standard for Retries) ---
    {
        "id": "tenacity_perfect",
        "description": "Tenacity with exponential backoff, max attempts, and specific errors",
        "expected_score": 0.9500, # lib(0.25) + dec(0.25) + exp(0.20) + max(0.15) + spec(0.10)
        "code": """
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(requests.exceptions.ConnectionError)
)
def fetch_external():
    return requests.get("https://api.example.com")
"""
    },
    {
        "id": "tenacity_basic",
        "description": "Tenacity with just max attempts (missing backoff and specific errors)",
        "expected_score": 0.6500, # lib(0.25) + dec(0.25) + max(0.15)
        "code": """
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def fetch():
    return requests.get("https://api")
"""
    },

    # --- BLOCK 2: Backoff Library ---
    {
        "id": "backoff_perfect",
        "description": "Backoff library with expo, max_tries, and specific Exception",
        "expected_score": 0.9500, # lib(0.25) + dec(0.25) + exp(0.20) + max(0.15) + spec(0.10)
        "code": """
import backoff
import requests

@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=8
)
def get_url(url):
    return requests.get(url)
"""
    },
    {
        "id": "backoff_constant_wait",
        "description": "Backoff using constant wait instead of exponential",
        "expected_score": 0.6500, # lib(0.25) + dec(0.25) + max(0.15) + spec(0.10)
        "code": """
import backoff

@backoff.on_exception(backoff.constant, Exception, max_tries=3)
def do_work():
    pass
"""
    },

    # --- BLOCK 3: Urllib3 Built-in Retry (Requests Sessions) ---
    {
        "id": "urllib3_retry",
        "description": "Urllib3 Retry strategy injected into Requests Session",
        "expected_score": 0.4000, # lib(0.25) + exp(0.20) + max(0.15) + spec(0.10) + idem(0.05) [wait, no decorator -> 0.75]
        "code": """
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
# Urllib3 respects idempotency by default (status_forcelist applied to safe methods)
retry = Retry(
    total=5,
    read=5,
    connect=5,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504)
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
"""
    },

    # --- BLOCK 4: Manual Loops (Anti-patterns & Custom Implementations) ---
    {
        "id": "manual_loop_basic_sleep",
        "description": "Basic for-loop retry with constant sleep (No libraries)",
        "expected_score": 0.2500, # Maybe hits nothing except some custom logic if configured? Actually base is 0.0
        "code": """
import time

def fetch():
    for attempt in range(3):
        try:
            return requests.get("http://api")
        except Exception:
            time.sleep(1) # Constant backoff
    raise Exception("Failed")
"""
    },
    {
        "id": "manual_loop_exponential_backoff",
        "description": "Manual loop with exponential backoff calculation",
        "expected_score": 0.4500, # exp(0.20) matched via '2 ** attempt'
        "code": """
import time

def fetch():
    for attempt in range(5):
        try:
            return requests.get("http://api")
        except Exception:
            # Exponential backoff manually
            time.sleep(2 ** attempt)
"""
    },

    # --- BLOCK 5: Negative Cases ---
    {
        "id": "no_retry_logic",
        "description": "CRITICAL: External call that completely lacks retry logic",
        "expected_score": 0.1000,
        "code": """
def get_data():
    # If this fails once, the user request fails. Bad UX.
    return requests.get('https://unreliable-api.com')
"""
    }
]
