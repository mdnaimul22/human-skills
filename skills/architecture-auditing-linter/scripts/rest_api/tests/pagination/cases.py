# =============================================================================
# Pagination Implementation — Test Dataset (Comprehensive ~20 Cases)
# Sources: Google API (page_token), Microsoft REST ($top, $skip), GitHub (Link)
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: Not a Collection Endpoint (Neutral Pass) ---
    {
        "id": "not_a_collection_endpoint",
        "description": "Endpoint returns a single item, pagination not applicable",
        "expected_score": 0.1000,
        "code": """
@app.get('/users/{id}')
def get_user(id):
    return db.query(User).get(id)
"""
    },
    {
        "id": "create_item_post",
        "description": "POST endpoint to create item, pagination not applicable",
        "expected_score": 1.0000,
        "code": """
@app.post('/items')
def create_item():
    item = db.insert(request.json)
    return jsonify(item), 201
"""
    },

    # --- BLOCK 2: Offset-based Pagination (Standard) ---
    {
        "id": "perfect_offset_pagination",
        "description": "Offset pagination with limit applied and metadata returned",
        "expected_score": 0.6500, # 0.35 (param) + 0.25 (limit) + 0.20 (meta) + 0.10 (no unlimited fetch)
        "code": """
@app.get('/users')
def list_users(limit: int = 10, offset: int = 0):
    users = db.query(User).limit(limit).offset(offset).all()
    return {
        "data": users, 
        "total": db.query(User).count(),
        "next": f"/users?limit={limit}&offset={offset+limit}"
    }
"""
    },
    {
        "id": "offset_no_metadata",
        "description": "Offset pagination applied but no metadata returned",
        "expected_score": 0.4500, # 0.35 + 0.25 + 0.10
        "code": """
@app.get('/articles')
def get_articles(page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    articles = db.query(Article).limit(per_page).offset(offset).all()
    return jsonify(articles) # No metadata
"""
    },
    {
        "id": "offset_params_ignored_limit",
        "description": "Params accepted but database limit not actually applied (Missing Limit Penalty)",
        "expected_score": 0.4000, # 0.35 + 0.10
        "code": """
@app.get('/products')
def get_products(limit: int = 50, offset: int = 0):
    # VULNERABLE: Fetches all, then slices in memory (very bad for DB)
    products = Product.objects.all()
    return {"data": products[offset:offset+limit], "total": len(products)}
"""
    },

    # --- BLOCK 3: Cursor-based Pagination (Google API Style) ---
    {
        "id": "perfect_cursor_pagination",
        "description": "Cursor pagination with page_token (Google API standard)",
        "expected_score": 0.4500, # 0.35(param) + 0.10(cursor) + 0.25(limit) + 0.20(meta) + 0.10(bonus)
        "code": """
@app.get('/messages')
def list_messages(page_size: int = 50, page_token: str = None):
    query = db.query(Message)
    if page_token:
        query = query.filter(Message.id > decode_token(page_token))
    
    messages = query.limit(page_size).all()
    next_token = encode_token(messages[-1].id) if messages else None
    
    return {
        "messages": messages,
        "next_page_token": next_token
    }
"""
    },
    {
        "id": "cursor_missing_metadata",
        "description": "Cursor used but next_token not returned (client gets stuck)",
        "expected_score": 0.5500, # 0.35 + 0.10 + 0.25 + 0.10
        "code": """
@app.get('/events')
def list_events(cursor: int = 0):
    # Limit applied, cursor accepted, but no metadata returned
    events = db.query(Event).filter(Event.id > cursor).limit(100).all()
    return jsonify(events) 
"""
    },

    # --- BLOCK 4: Microsoft REST API Guidelines (OData Style) ---
    {
        "id": "odata_top_skip_pagination",
        "description": "OData style $top and $skip pagination",
        "expected_score": 0.4500, # 0.35 + 0.25 + 0.20 + 0.10
        "code": """
@app.get('/employees')
def list_employees():
    top = int(request.args.get('$top', 10))
    skip = int(request.args.get('$skip', 0))
    
    data = db.employees.find().skip(skip).limit(top)
    return jsonify({
        "value": list(data),
        "@odata.count": db.employees.count_documents({})
    })
"""
    },

    # --- BLOCK 5: GitHub API Conventions (Link Headers) ---
    {
        "id": "github_link_header_pagination",
        "description": "Pagination metadata sent via Link header",
        "expected_score": 0.4500,
        "code": """
@app.get('/repos')
def list_repos(page: int = 1, per_page: int = 30):
    offset = (page - 1) * per_page
    repos = db.query(Repo).limit(per_page).offset(offset).all()
    
    resp = jsonify(repos)
    # Metadata in headers
    resp.headers['Link'] = f'<https://api.github.com/repos?page={page+1}>; rel="next"'
    return resp
"""
    },

    # --- BLOCK 6: Unbounded Collection Fetches (OWASP DOS Vulnerability) ---
    {
        "id": "unbounded_fetch_flask",
        "description": "CRITICAL: Fetching entire table into memory without limits",
        "expected_score": 0.2000,
        "code": """
@app.get('/logs')
def get_all_logs():
    # VULNERABLE: No limit, offset, or parameters. DB could return millions of rows.
    logs = db.query(Log).all()
    return jsonify(logs)
"""
    },
    {
        "id": "unbounded_fetch_django",
        "description": "CRITICAL: Django fetching all objects",
        "expected_score": 0.0000,
        "code": """
@app.get('/transactions')
def get_transactions():
    txns = Transaction.objects.all()
    return jsonify(list(txns))
"""
    },
    {
        "id": "unbounded_fetch_raw_sql",
        "description": "CRITICAL: Raw SQL SELECT * without LIMIT",
        "expected_score": 0.3000,
        "code": """
@app.get('/data')
def get_data():
    cursor.execute("SELECT * FROM large_table")
    return jsonify(cursor.fetchall())
"""
    },

    # --- BLOCK 7: Edge Cases and Partial Implementations ---
    {
        "id": "limit_hardcoded_no_params",
        "description": "No pagination parameters accepted, but safe DB limit hardcoded",
        "expected_score": 0.6500, # limit applied (0.25) + no unbounded fetch (0.10)
        "code": """
@app.get('/latest_news')
def get_latest_news():
    # Safe, but not true pagination
    news = db.query(News).order_by(News.date.desc()).limit(10).all()
    return jsonify(news)
"""
    },
    {
        "id": "params_accepted_no_limit_no_metadata",
        "description": "Pagination parameters in signature but unused, unlimited fetch occurs",
        "expected_score": 0.2000, # param present (0.35)
        "code": """
@app.get('/files')
def list_files(page: int = 1, size: int = 50):
    # Developer forgot to apply the limit!
    files = db.query(File).all()
    return jsonify(files)
"""
    }
]
