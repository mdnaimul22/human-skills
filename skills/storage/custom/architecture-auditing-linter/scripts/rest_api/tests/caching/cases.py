# =============================================================================
# Caching Implementation — Test Dataset (Comprehensive ~20 Cases)
# Sources: Google API Design Guide, Microsoft REST Guidelines, GitHub API Conventions
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: HTTP Level Caching (Google & GitHub Conventions) ---
    {
        "id": "google_api_etag_cache_control",
        "description": "Google API style: ETag and Cache-Control headers returned for efficient caching",
        "expected_score": 0.2500, # Base: will be calibrated
        "code": """
@app.route('/resources/<id>')
def get_resource(id):
    data = db.get_resource(id)
    response = jsonify(data)
    response.headers['ETag'] = compute_etag(data)
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response
"""
    },
    {
        "id": "github_304_not_modified",
        "description": "GitHub style: Checking If-None-Match header and returning 304",
        "expected_score": 0.2500,
        "code": """
@app.route('/repos')
def get_repos():
    client_etag = request.headers.get('If-None-Match')
    current_etag = get_latest_repo_etag()
    if client_etag == current_etag:
        return '', 304 # Not Modified
    resp = jsonify(get_repos_data())
    resp.headers['ETag'] = current_etag
    return resp
"""
    },
    {
        "id": "vary_header_split",
        "description": "Vary header used to split cache based on Accept-Encoding",
        "expected_score": 0.2500,
        "code": """
@app.get('/articles')
def articles():
    resp = jsonify(fetch_articles())
    resp.headers['Vary'] = 'Accept-Encoding'
    resp.headers['Cache-Control'] = 'public, max-age=600'
    return resp
"""
    },
    {
        "id": "expires_and_last_modified",
        "description": "Legacy HTTP caching using Expires and Last-Modified",
        "expected_score": 0.2500,
        "code": """
@app.get('/assets')
def assets():
    resp = Response(load_asset())
    resp.headers['Last-Modified'] = asset.mtime
    resp.headers['Expires'] = 'Wed, 21 Oct 2026 07:28:00 GMT'
    return resp
"""
    },

    # --- BLOCK 2: App Level Caching (Redis/Memcached/Frameworks) ---
    {
        "id": "flask_caching_full",
        "description": "Flask-Caching with Redis backend, set, get, and delete",
        "expected_score": 0.6000,
        "code": """
from flask_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'redis'})

def process():
    val = cache.get('my_key')
    if not val:
        val = compute()
        cache.set('my_key', val)
    return val

def invalidate():
    cache.delete('my_key')
"""
    },
    {
        "id": "fastapi_cache_decorator",
        "description": "FastAPI Cache decorator usage",
        "expected_score": 0.3500,
        "code": """
from fastapi_cache.decorator import cache

@app.get("/items")
@cache(expire=60)
async def get_items():
    return await db.fetch_all()
"""
    },
    {
        "id": "raw_redis_caching",
        "description": "Direct Redis client usage for caching",
        "expected_score": 0.4500,
        "code": """
import redis
r = redis.Redis()

def get_user(id):
    cached = r.get(f"user:{id}")
    if cached: return cached
    user = db.query(id)
    r.setex(f"user:{id}", 3600, user)
    return user
"""
    },
    {
        "id": "memcached_usage",
        "description": "Memcached usage with get and set",
        "expected_score": 0.2000,
        "code": """
import memcache
mc = memcache.Client(['127.0.0.1:11211'])

def fetch():
    data = mc.get('data_key')
    if not data:
        data = load_data()
        mc.set('data_key', data)
    return data
"""
    },
    {
        "id": "python_lru_cache",
        "description": "Builtin functools lru_cache decorator",
        "expected_score": 0.1500,
        "code": """
from functools import lru_cache

@lru_cache(maxsize=128)
def get_heavy_computation(param):
    return run_math(param)
"""
    },
    {
        "id": "cachetools_ttl_cache",
        "description": "Using cachetools TTLCache",
        "expected_score": 0.3500,
        "code": """
from cachetools import cached, TTLCache
cache = TTLCache(maxsize=100, ttl=300)

@cached(cache)
def get_weather():
    return api.fetch()
"""
    },
    {
        "id": "dogpile_cache_region",
        "description": "Dogpile cache region to prevent cache stampede",
        "expected_score": 0.2000,
        "code": """
from dogpile.cache import make_region

region = make_region().configure('dogpile.cache.redis')

@region.cache_on_arguments()
def load_stuff():
    return slow_db_query()
"""
    },
    {
        "id": "django_cache_page",
        "description": "Django view decorator cache_page",
        "expected_score": 0.1500,
        "code": """
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)
def my_view(request):
    return HttpResponse("Hello")
"""
    },

    # --- BLOCK 3: Security & Sensitivity (OWASP API Security) ---
    {
        "id": "auth_sensitive_no_store_pass",
        "description": "Auth-sensitive endpoint correctly setting Cache-Control: no-store",
        "expected_score": 0.3500,
        "code": """
@app.get('/api/v1/profile')
def get_profile():
    if not request.user.is_authenticated:
        return 401
    resp = jsonify(request.user.profile)
    resp.headers['Cache-Control'] = 'no-store, no-cache, private'
    return resp
"""
    },
    {
        "id": "auth_sensitive_missing_no_store_fail",
        "description": "Auth-sensitive endpoint missing no-store, risking PII leak",
        "expected_score": 0.1000,
        "code": """
@app.get('/api/v1/wallet')
def get_wallet():
    # Sensitive data fetched using Authorization header
    token = request.headers.get('Authorization')
    user_data = verify_and_fetch(token)
    return jsonify(user_data) # NO CACHE HEADERS!
"""
    },
    {
        "id": "auth_current_user_no_store",
        "description": "Using current_user variable and applying no-store",
        "expected_score": 0.3500,
        "code": """
def get_settings():
    u = current_user
    res = Response(u.settings)
    res.headers['Cache-Control'] = 'no-store'
    return res
"""
    },

    # --- BLOCK 4: Cache Invalidation Patterns ---
    {
        "id": "explicit_cache_invalidation_webhook",
        "description": "Webhook endpoint flushing/clearing cache",
        "expected_score": 0.1500,
        "code": """
@app.post('/webhook/update')
def handle_update():
    process_update()
    cache.clear()
    return "OK"
"""
    },
    {
        "id": "redis_delete_eviction",
        "description": "Evicting specific keys on object update",
        "expected_score": 0.3200,
        "code": """
import redis
r = redis.Redis()

@app.put('/item/<id>')
def update_item(id):
    db.update(id, request.json)
    r.delete(f"item:{id}")
    return "Updated"
"""
    },

    # --- BLOCK 5: Negative & Edge Cases ---
    {
        "id": "no_caching_at_all",
        "description": "Completely naive endpoint without caching",
        "expected_score": 0.2000,
        "code": """
@app.get('/articles')
def fetch_articles():
    # heavy DB hit every time
    return jsonify(db.execute("SELECT * FROM articles").fetchall())
"""
    },
    {
        "id": "single_cache_operation_partial",
        "description": "Only setting cache but never reading it (weird edge case)",
        "expected_score": 0.1200,
        "code": """
def do_stuff():
    val = process()
    cache.set('key', val)
    return val
"""
    },
    {
        "id": "caching_private_header",
        "description": "Cache-Control set to private for user-specific caching",
        "expected_score": 0.2500,
        "code": """
@app.get('/dashboard')
def dash():
    resp = jsonify(get_dash())
    resp.headers['Cache-Control'] = 'private, max-age=300'
    return resp
"""
    }
]
