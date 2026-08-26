# =============================================================================
# Rate Limiting Implementation — Test Dataset (Comprehensive ~20 Cases)
# Sources: Google API (429 Retry-After), GitHub (X-RateLimit headers)
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: Standard Library Usage (Flask, FastAPI, Django) ---
    {
        "id": "flask_limiter_perfect",
        "description": "Flask-Limiter with multiple decorators (Global + Specific)",
        "expected_score": 0.5000, # lib(0.25) + decorators>=2(0.25)
        "code": """
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day"])

@app.route('/login')
@limiter.limit("5 per minute")
@limiter.limit("1 per second")
def login():
    return "OK"
"""
    },
    {
        "id": "fastapi_slowapi",
        "description": "FastAPI SlowAPI usage",
        "expected_score": 0.6000, # lib(0.25) + decorator==1(0.15)
        "code": """
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/home")
@limiter.limit("5/minute")
async def homepage(request: Request):
    return {"msg": "Hello"}
"""
    },
    {
        "id": "django_ratelimit",
        "description": "Django ratelimit decorator",
        "expected_score": 0.4000,
        "code": """
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', block=True)
def my_view(request):
    return HttpResponse("OK")
"""
    },

    # --- BLOCK 2: Headers and Standard 429 Responses (GitHub & Google Specs) ---
    {
        "id": "github_style_headers",
        "description": "Custom rate limiter returning GitHub style headers and 429",
        "expected_score": 0.6000, # custom logic(0.15) + 429(0.10) + headers(0.10)
        "code": """
@app.get("/repos")
def get_repos():
    client_ip = request.remote_addr
    count = redis.incr(f"rate:{client_ip}")
    
    if count > 100:
        resp = jsonify(error="Rate limit exceeded")
        resp.headers['Retry-After'] = 60
        resp.headers['X-RateLimit-Remaining'] = 0
        return resp, 429
        
    resp = jsonify(data)
    resp.headers['X-RateLimit-Limit'] = 100
    resp.headers['X-RateLimit-Remaining'] = 100 - count
    return resp
"""
    },
    {
        "id": "google_retry_after",
        "description": "Google API style: 429 Too Many Requests with Retry-After header",
        "expected_score": 0.2000, # custom(0.15) + 429(0.10) + header(0.10)
        "code": """
def check_limit():
    if over_limit():
        abort(429, headers={'Retry-After': '120'})
"""
    },

    # --- BLOCK 3: Middleware Implementation ---
    {
        "id": "middleware_rate_limiter",
        "description": "Global middleware enforcing rate limits across all routes",
        "expected_score": 0.1000, # middleware(0.20) + 429(0.10)
        "code": """
@app.before_request
def rate_limit_middleware():
    ip = request.remote_addr
    if redis.get(f"block:{ip}"):
        return "Too Many Requests", 429
"""
    },
    {
        "id": "fastapi_middleware_limiter",
        "description": "FastAPI HTTP middleware for rate limiting",
        "expected_score": 0.3500,
        "code": """
@app.middleware("http")
async def apply_rate_limit(request: Request, call_next):
    client = request.client.host
    if is_rate_limited(client):
        return Response("Rate limit exceeded", status_code=429)
    return await call_next(request)
"""
    },

    # --- BLOCK 4: Custom Token Bucket / Sliding Window (Custom Logic) ---
    {
        "id": "custom_redis_sliding_window",
        "description": "Redis-based sliding window rate limiter logic",
        "expected_score": 0.1500, # custom(0.15)
        "code": """
def is_allowed(user_id):
    current_time = time.time()
    redis.zremrangebyscore(f"window:{user_id}", 0, current_time - 60)
    request_count = redis.zcard(f"window:{user_id}")
    
    if request_count >= 50:
        return False
        
    redis.zadd(f"window:{user_id}", {current_time: current_time})
    return True
"""
    },
    {
        "id": "per_user_rate_limiting",
        "description": "Custom rate limit applied per authenticated user (bonus points)",
        "expected_score": 0.1500, # custom(0.15) + per_user(0.05)
        "code": """
@app.get('/dashboard')
def dashboard():
    user_id = current_user.id
    if redis.get(f"limit:{user_id}") > 100:
        return "Blocked"
    redis.incr(f"limit:{user_id}")
    return "Welcome"
"""
    },

    # --- BLOCK 5: Negative & Edge Cases (Failures) ---
    {
        "id": "no_rate_limiting_at_all",
        "description": "CRITICAL: No rate limiting on public endpoint (DOS Vulnerability)",
        "expected_score": 0.0500,
        "code": """
@app.post('/register')
def register():
    user = db.create_user(request.json)
    return jsonify(user)
"""
    },
    {
        "id": "wrong_status_code_for_limit",
        "description": "Rate limiting logic present, but returns 400 instead of 429",
        "expected_score": 0.0000, # custom logic(0.15), misses 429 bonus
        "code": """
def check_rate():
    if redis.get('hits') > 10:
        return "Too fast", 400 # Wrong status code!
"""
    },
    {
        "id": "sleep_instead_of_429",
        "description": "Bad practice: sleeping the thread instead of returning 429",
        "expected_score": 0.0500,
        "code": """
@app.get('/heavy')
def heavy_job():
    if redis.get('active_jobs') > 5:
        time.sleep(10) # Holding the connection!
    return "Done"
"""
    }
]
