# =============================================================================
# Idempotency Implementation — Test Dataset
#
# Sources:
#   - Google API Design Guide (AIP-0155: request deduplication)
#   - Microsoft REST API Guidelines §Idempotency
#   - GitHub REST API conventions (PUT/DELETE idempotent by design)
#   - RFC 7231 §4.2.2 (Idempotent Methods)
#   - Stripe API (Idempotency-Key header pattern)
#
# Scoring model (additive, max 1.0):
#   0.30 — Idempotency-Key header read and used
#   0.25 — PUT endpoint present (idempotent by RFC 7231)
#   0.20 — Deduplication logic (redis/cache/DB check)
#   0.15 — 409 Conflict on duplicate key
#   0.10 — Idempotency-Key returned in response header
#
# Baseline:
#   0.50 — No mutation endpoints (GET-only code — cannot assess idempotency)
#   0.00 — POST without any idempotency mechanism
# =============================================================================

TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Full Idempotency (score = 0.9)
    # Idempotency-Key + dedup check + 409 + PUT present.
    # =========================================================================

    {
        "id": "full_idempotency_key_dedup",
        "description": "POST with Idempotency-Key, Redis dedup check, 409 conflict, PUT endpoint",
        "expected_score": 0.9,
        "code": """
@app.post("/payments")
def create_payment():
    key = request.headers.get("Idempotency-Key")
    if redis.get(key):
        return jsonify(error="duplicate request"), 409
    result = db.insert(payment)
    redis.set(key, result.id, ex=86400)
    return jsonify(result), 201

@app.put("/users/{id}")
def update_user(id):
    db.replace(id, request.json)
    return jsonify(), 200
""",
    },

    {
        "id": "full_idempotency_stripe_pattern",
        "description": "Stripe-pattern: Idempotency-Key header, DB get_or_create dedup, 409 on collision",
        "expected_score": 0.7,
        "code": """
@app.post("/charges")
def create_charge():
    idempotency_key = request.headers.get("Idempotency-Key")
    existing = IdempotencyStore.objects.filter(key=idempotency_key).first()
    if existing:
        return jsonify(existing.response_data), 409
    charge = process_charge(request.json)
    IdempotencyStore.objects.create(key=idempotency_key, response_data=charge)
    return jsonify(charge), 201

@app.put("/subscriptions/{id}")
def update_subscription(id):
    db.replace(id, request.json)
    return jsonify(), 200
""",
    },

    # =========================================================================
    # BLOCK 2 — PUT Only, No Idempotency-Key (score = 0.25)
    # PUT is idempotent by RFC 7231 — partial credit.
    # =========================================================================

    {
        "id": "put_only_idempotent",
        "description": "PUT endpoint only — idempotent by RFC 7231, no Idempotency-Key header",
        "expected_score": 0.25,
        "code": """
@app.put("/items/{id}")
def update_item(id):
    db.replace(id, request.json)
    return jsonify(), 200
""",
    },

    {
        "id": "put_delete_no_key",
        "description": "PUT + DELETE endpoints — both idempotent by RFC 7231, no explicit key",
        "expected_score": 0.25,
        "code": """
@app.put("/orders/{id}")
def update_order(id):
    db.replace(id, request.json)
    return jsonify(), 200

@app.delete("/orders/{id}")
def cancel_order(id):
    db.delete(id)
    return jsonify(), 204
""",
    },

    # =========================================================================
    # BLOCK 3 — POST Without Idempotency (score = 0.0)
    # Mutation endpoint with no idempotency mechanism — creates duplicates.
    # =========================================================================

    {
        "id": "post_no_idempotency",
        "description": "POST endpoint with no Idempotency-Key, no dedup — duplicate-safe violation",
        "expected_score": 0.0,
        "code": """
@app.post("/orders")
def create_order():
    order = db.insert(request.json)
    return jsonify(order), 201
""",
    },

    {
        "id": "post_patch_no_key",
        "description": "POST + PATCH with no idempotency mechanism — both non-idempotent",
        "expected_score": 0.0,
        "code": """
@app.post("/invoices")
def create_invoice():
    inv = db.insert(request.json)
    return jsonify(inv), 201

@app.patch("/invoices/{id}")
def patch_invoice(id):
    db.update(id, request.json)
    return jsonify(), 200
""",
    },

    # =========================================================================
    # BLOCK 4 — GET-Only (score = 0.5 neutral)
    # No mutation endpoints — idempotency not assessable.
    # =========================================================================

    {
        "id": "get_only_neutral",
        "description": "GET-only routes — idempotency not applicable, neutral score",
        "expected_score": 0.5,
        "code": """
@app.get("/users")
def list_users():
    return jsonify(users=db.all())

@app.get("/users/{id}")
def get_user(id):
    return jsonify(user=db.get(id))
""",
    },

]
