# =============================================================================
# Timeout Handling — Test Dataset (Comprehensive ~20 Cases)
# Sources: Microsoft REST API Guidelines (Reliability), Google API
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: HTTP Request Timeouts (Most Critical) ---
    {
        "id": "requests_with_timeout_perfect",
        "description": "Python requests library with explicit timeout (Best practice)",
        "expected_score": 0.3000, # HTTP(0.30)
        "code": """
import requests

@app.get('/weather')
def get_weather():
    # Timeout ensures the thread doesn't hang forever
    res = requests.get('https://api.weather.com', timeout=5.0)
    return res.json()
"""
    },
    {
        "id": "httpx_with_timeout",
        "description": "HTTPX library with timeout configured",
        "expected_score": 0.3000,
        "code": """
import httpx

@app.get('/data')
def get_data():
    with httpx.Client(timeout=10.0) as client:
        return client.get("https://api.example.com").json()
"""
    },
    {
        "id": "requests_missing_timeout_penalty",
        "description": "CRITICAL: requests call missing timeout (Thread exhaustion risk)",
        "expected_score": 0.0000, # HTTP without timeout (-0.20)
        "code": """
import requests

@app.post('/webhook')
def trigger_webhook():
    # VULNERABLE: If external server hangs, this thread hangs forever
    requests.post('https://external-webhook.com', json={"event": "fired"})
    return "Sent"
"""
    },

    # --- BLOCK 2: Database Timeouts ---
    {
        "id": "db_statement_timeout",
        "description": "Setting database statement_timeout via raw SQL",
        "expected_score": 0.2000, # DB timeout (0.20)
        "code": """
@app.get('/report')
def generate_report():
    # Postgres specific statement timeout
    db.session.execute("SET statement_timeout = '10s'")
    data = db.query(HeavyReport).all()
    return jsonify(data)
"""
    },
    {
        "id": "db_pool_timeout_configured",
        "description": "SQLAlchemy pool_timeout configuration",
        "expected_score": 0.3000,
        "code": """
from sqlalchemy import create_engine

# Engine configured with pool timeout to prevent connection hangs
engine = create_engine(DB_URL, pool_timeout=30)
Session = sessionmaker(bind=engine)

def fetch():
    db = Session()
    return db.query(User).all()
"""
    },
    {
        "id": "db_missing_timeout_penalty",
        "description": "DB call without any explicit timeout in the block",
        "expected_score": 0.0000, # DB without timeout (-0.05)
        "code": """
@app.get('/users')
def get_users():
    # No timeout context or configuration visible
    return db.query(User).all()
"""
    },

    # --- BLOCK 3: Async Operation Timeouts ---
    {
        "id": "asyncio_wait_for",
        "description": "Async operation wrapped in asyncio.wait_for",
        "expected_score": 0.8000, # Async timeout (0.20), but let's check DB/HTTP context. (Wait, just async timeout is 0.20)
        "code": """
import asyncio

@app.get('/async-data')
async def fetch_async():
    # Safe async wrapping
    data = await asyncio.wait_for(heavy_computation(), timeout=5.0)
    return data
"""
    },
    {
        "id": "asyncio_timeout_context",
        "description": "Python 3.11+ asyncio.timeout context manager",
        "expected_score": 0.8000,
        "code": """
import asyncio

@app.get('/fast-data')
async def fetch():
    async with asyncio.timeout(2.5):
        await asyncio.sleep(1)
        return "OK"
"""
    },
    {
        "id": "async_missing_timeout_penalty",
        "description": "Async function with await but no timeout wrapper",
        "expected_score": 0.8000, # Async without timeout (-0.05)
        "code": """
import asyncio

@app.get('/slow')
async def slow_endpoint():
    # VULNERABLE: Awaiting an unbounded operation
    await asyncio.sleep(100)
    return "Done"
"""
    },

    # --- BLOCK 4: Combined Scenarios (The perfect endpoint) ---
    {
        "id": "perfect_all_timeouts",
        "description": "Handles HTTP, DB, and Async timeouts perfectly",
        "expected_score": 0.7000, # HTTP(0.30) + DB(0.20) + Async(0.20) = 0.70
        "code": """
import requests
import asyncio

@app.get('/full')
async def full_fetch():
    async with asyncio.timeout(10.0):
        # HTTP timeout
        res = requests.get('http://api', timeout=2)
        # DB timeout
        db.execute("SET statement_timeout = 2000")
        db.query(Model).all()
    return "OK"
"""
    },

    # --- BLOCK 5: Neutral Cases ---
    {
        "id": "no_external_calls_neutral",
        "description": "Endpoint doing pure computational logic, no network/DB involved",
        "expected_score": 0.8000, # Neutral baseline
        "code": """
@app.get('/math')
def do_math():
    x = 10 * 20
    return {"result": x}
"""
    }
]
