# =============================================================================
# API Versioning Strategy — Test Dataset
# Sources: Stripe (URL), GitHub (media-type), Google AIP (URL+sunset)
# =============================================================================

TEST_CASES = [

    # --- BLOCK 1: Perfect URL Versioning ---
    {
        "id": "perfect_url_versioning",
        "description": "All endpoints consistently use /v1/ at root with sunset headers",
        "expected_score": 0.85,
        "code": """
@app.get("/v1/users")
async def list_users():
    return users

@app.get("/v1/users/{id}")
async def get_user(id: int):
    return user

@app.post("/v1/orders")
async def create_order():
    return order

@app.get("/v1/legacy", deprecated=True)
async def legacy():
    response.headers["Sunset"] = "2025-12-31"
    return data
"""
    },
    {
        "id": "url_version_no_sunset",
        "description": "Consistent /v1/ versioning but no deprecation headers",
        "expected_score": 0.70,
        "code": """
@app.get("/v1/products")
async def list_products():
    return products

@app.get("/v1/products/{id}")
async def get_product(id: int):
    return product

@app.post("/v1/products")
async def create_product():
    return product
"""
    },

    # --- BLOCK 2: Header-Based Versioning ---
    {
        "id": "header_versioning",
        "description": "Header-based versioning using Accept-Version",
        "expected_score": 0.65,
        "code": """
@app.get("/users")
async def list_users(request):
    version = request.headers["Accept-Version"]
    if version == "2":
        return users_v2
    return users_v1

@app.get("/products")
async def list_products(request):
    api_version = request.headers["API-Version"]
    return products
"""
    },
    {
        "id": "header_version_with_sunset",
        "description": "Header versioning with deprecation signals",
        "expected_score": 0.80,
        "code": """
@app.get("/users")
async def list_users(request):
    version = request.headers["Accept-Version"]
    if version == "1":
        response.headers["Sunset"] = "2025-06-01"
        response.headers["Deprecation"] = "true"
    return users
"""
    },

    # --- BLOCK 3: No Versioning ---
    {
        "id": "no_versioning_at_all",
        "description": "No versioning strategy detected",
        "expected_score": 0.0,
        "code": """
@app.get("/users")
async def list_users():
    return users

@app.post("/users")
async def create_user():
    return user

@app.delete("/users/{id}")
async def delete_user(id: int):
    return {"deleted": True}
"""
    },
    {
        "id": "no_versioning_small",
        "description": "Tiny code, no versioning",
        "expected_score": 0.0,
        "code": """
@app.get("/health")
def health():
    return {"ok": True}
"""
    },

    # --- BLOCK 4: Inconsistent Versioning ---
    {
        "id": "partial_versioning",
        "description": "Some endpoints versioned, others not",
        "expected_score": 0.60,
        "code": """
@app.get("/v1/users")
async def list_users():
    return users

@app.get("/v1/users/{id}")
async def get_user(id: int):
    return user

@app.get("/products")
async def list_products():
    return products

@app.post("/orders")
async def create_order():
    return order
"""
    },
    {
        "id": "version_mid_path",
        "description": "Version appears mid-path, not at root",
        "expected_score": 0.50,
        "code": """
@app.get("/users/v1/active")
async def get_active_users():
    return users

@app.get("/products/v2/featured")
async def get_featured():
    return products
"""
    },

    # --- BLOCK 5: Multiple Version Strategies (Penalty) ---
    {
        "id": "url_plus_query_mixed",
        "description": "Mixing URL versioning with query param versioning",
        "expected_score": 0.50,
        "code": """
@app.get("/v1/users")
async def list_users():
    return users

@app.get("/v1/users/{id}")
async def get_user(id: int):
    return user

@app.get("/products?version=2")
async def list_products():
    version = request.args.get('version')
    return products
"""
    },

    # --- BLOCK 6: API Prefix Versioning ---
    {
        "id": "api_prefix_versioned",
        "description": "/api/v1/ prefix — standard enterprise pattern",
        "expected_score": 0.70,
        "code": """
@app.get("/api/v1/users")
async def list_users():
    return users

@app.get("/api/v1/users/{id}")
async def get_user(id: int):
    return user

@app.post("/api/v1/orders")
async def create_order():
    return order
"""
    },

    # --- BLOCK 7: Multi-Version Migration ---
    {
        "id": "multi_version_migration",
        "description": "Both v1 and v2 endpoints — proper migration",
        "expected_score": 0.85,
        "code": """
@app.get("/v1/users", deprecated=True)
async def list_users_v1():
    return users_v1

@app.get("/v2/users")
async def list_users_v2():
    return users_v2

@app.get("/v2/users/{id}")
async def get_user_v2(id: int):
    return user_v2
"""
    },

    # --- BLOCK 8: Non-Python / Edge Cases ---
    {
        "id": "no_code_at_all",
        "description": "Empty or non-API code",
        "expected_score": 0.0,
        "code": """
def helper_function():
    return 42

x = helper_function()
"""
    },
]
