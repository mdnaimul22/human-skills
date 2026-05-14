TEST_CASES = [
    {
        'id': 'perfect_status_codes',
        'description': 'Uses 201 for creation, 401 for auth, 409 for conflict.',
        'expected_score': 1.0000,
        'code': """
@app.post("/users")
def create_user(data: UserCreate):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    if user_exists(data.email):
        raise HTTPException(status_code=409, detail="User already exists")
    user = db.add(data)
    return Response(status=201)
"""
    },
    {
        'id': 'no_explicit_status',
        'description': 'No explicit status codes, relies on framework defaults.',
        'expected_score': 0.4000,
        'code': """
@app.get("/users/{id}")
def get_user(id):
    user = db.get(id)
    return user
"""
    },
    {
        'id': 'overuse_200',
        'description': 'Uses 200 for everything including errors.',
        'expected_score': 0.0000,
        'code': """
def create_user():
    if missing_token:
        return jsonify(error="missing token"), 200
    if duplicate:
        return jsonify(error="duplicate"), 200
    db.add()
    return jsonify(success=True), 200
"""
    },
    {
        'id': 'partial_correct',
        'description': 'Returns 200 when 404 is expected.',
        'expected_score': 0.0000,
        'code': """
def check_user():
    if not_found:
        return "not found", 200
    return "ok", 200
"""
    },
    {
        'id': 'variety_bonus_2',
        'description': 'Good usage with two distinct status codes.',
        'expected_score': 1.0000,
        'code': """
def get_user():
    if not_found:
        abort(404)
    return jsonify(), 200
"""
    },
    {
        'id': 'server_error_500',
        'description': 'Properly catches exceptions and returns 500.',
        'expected_score': 1.0000,
        'code': """
def fetch_data():
    try:
        do_work()
    except Exception:
        # internal server error
        abort(500)
    return "ok", 200
"""
    },
    {
        'id': 'validation_400_422',
        'description': 'Returns 400/422 for validation errors.',
        'expected_score': 1.0000,
        'code': """
def submit():
    if invalid_payload:
        return jsonify(error="validation error"), 422
    db.insert()
    return "ok", 201
"""
    },
    {
        'id': 'permission_403',
        'description': 'Returns 403 for permission denied.',
        'expected_score': 1.0000,
        'code': """
def delete_file():
    if not allowed:
        return "permission denied", 403
    db.delete()
    return "", 204
"""
    },
]
