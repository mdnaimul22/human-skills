# =============================================================================
# HTTP Method Correctness — Extended Test Dataset
# Scope: ONLY evaluates whether the HTTP method matches the operation semantics.
# Out of scope: naming conventions, caching, error handling, rate limiting.
# =============================================================================
#
# Score Legend:
#   1.0  → Perfect match  : method and operation are semantically aligned
#   0.8  → Minor mismatch : method is acceptable but not ideal
#   0.6  → Moderate misuse: method is wrong but operation is harmless
#   0.5  → Ambiguous      : method has both correct and incorrect signals
#   0.0  → Major violation: method and operation are completely opposite
# =============================================================================

EXTENDED_TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Async / Await Patterns
    # Same violations as sync, but in async context.
    # Expectation: async keyword must NOT change the score.
    # =========================================================================

    {
        "id": "async_get_clean_read",
        "description": "Async FastAPI GET with a clean read — no side effects",
        "code": """
@app.get("/products/{id}")
async def get_product(id: str):
    product = await db.products.find_one({"id": id})
    return product
""",
        "expected_score": 1.0
    },

    {
        "id": "async_get_with_delete",
        "description": "Async GET that awaits a delete call (Major Violation)",
        "code": """
@app.get("/purge/{id}")
async def purge_record(id: str):
    await db.records.delete_one({"id": id})
    return {"status": "purged"}
""",
        "expected_score": 0.0
    },

    {
        "id": "async_post_insert",
        "description": "Async POST that awaits an insert — correct usage",
        "code": """
@app.post("/orders")
async def create_order(order: OrderSchema):
    result = await db.orders.insert_one(order.dict())
    return {"id": str(result.inserted_id)}
""",
        "expected_score": 1.0
    },

    {
        "id": "async_get_with_update",
        "description": "Async GET that awaits an update_one call (Major Violation)",
        "code": """
@app.get("/activate/{id}")
async def activate_user(id: str):
    await db.users.update_one({"id": id}, {"$set": {"active": True}})
    return {"activated": True}
""",
        "expected_score": 0.0
    },

    {
        "id": "async_delete_read_only",
        "description": "Async DELETE route that only reads — no actual deletion (Misuse)",
        "code": """
@app.delete("/check/{id}")
async def check_record(id: str):
    record = await db.records.find_one({"id": id})
    return {"exists": bool(record)}
""",
        "expected_score": 0.6
    },

    {
        "id": "async_patch_correct",
        "description": "Async PATCH that awaits a partial update — correct usage",
        "code": """
@app.patch("/users/{id}/email")
async def update_email(id: str, payload: EmailUpdateSchema):
    await db.users.update_one({"id": id}, {"$set": {"email": payload.email}})
    return {"updated": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "async_put_full_replace",
        "description": "Async PUT that replaces an entire document — correct usage",
        "code": """
@app.put("/profiles/{id}")
async def replace_profile(id: str, profile: ProfileSchema):
    await db.profiles.replace_one({"id": id}, profile.dict())
    return {"replaced": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "async_get_view_counter",
        "description": "Async GET that reads but also increments a view counter (Ambiguous)",
        "code": """
@app.get("/posts/{id}")
async def get_post(id: str):
    post = await db.posts.find_one({"id": id})
    await db.posts.update_one({"id": id}, {"$inc": {"views": 1}})
    return post
""",
        "expected_score": 0.5
    },

    # =========================================================================
    # BLOCK 2 — Bulk Operations
    # insert_many, delete_many, update_many in various method contexts.
    # =========================================================================

    {
        "id": "post_insert_many",
        "description": "POST route using insert_many for bulk creation — correct",
        "code": """
@app.post("/products/bulk")
def bulk_create_products(products: list[ProductSchema]):
    db.products.insert_many([p.dict() for p in products])
    return {"inserted": len(products)}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_delete_many",
        "description": "GET route calling delete_many (Major Violation)",
        "code": """
@app.get("/admin/cleanup")
def cleanup_old_records():
    db.logs.delete_many({"expired": True})
    return {"status": "cleaned"}
""",
        "expected_score": 0.0
    },

    {
        "id": "delete_delete_many",
        "description": "DELETE route calling delete_many — semantically correct",
        "code": """
@app.delete("/sessions/expired")
def remove_expired_sessions():
    db.sessions.delete_many({"expires_at": {"$lt": now()}})
    return {"status": "cleared"}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_update_many",
        "description": "GET route calling update_many on all records (Major Violation)",
        "code": """
@app.get("/admin/reset-flags")
def reset_all_flags():
    db.users.update_many({}, {"$set": {"flag": False}})
    return {"reset": True}
""",
        "expected_score": 0.0
    },

    {
        "id": "put_update_many",
        "description": "PUT route calling update_many — acceptable bulk replace semantics",
        "code": """
@app.put("/inventory/restock")
def restock_all(payload: RestockSchema):
    db.inventory.update_many({}, {"$set": {"stock": payload.default_stock}})
    return {"restocked": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "post_bulk_read_only",
        "description": "POST route that only reads many records — misuse of POST",
        "code": """
@app.post("/reports/export")
def export_report(filters: dict):
    records = list(db.sales.find(filters))
    return {"data": records}
""",
        "expected_score": 0.6
    },

    # =========================================================================
    # BLOCK 3 — External API / Third-party Side Effects
    # The mutation is not in the local DB but via an external service call.
    # =========================================================================

    {
        "id": "get_sends_email",
        "description": "GET route that triggers an email send (external mutation)",
        "code": """
@app.get("/notify/{user_id}")
def notify_user(user_id: str):
    user = db.users.find_one({"id": user_id})
    email_client.send(to=user["email"], subject="Hello")
    return {"sent": True}
""",
        "expected_score": 0.0
    },

    {
        "id": "post_sends_email",
        "description": "POST route that triggers an email — correct, POST implies action",
        "code": """
@app.post("/notifications/send")
def send_notification(payload: NotificationSchema):
    email_client.send(to=payload.email, subject=payload.subject, body=payload.body)
    return {"sent": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_calls_payment_api",
        "description": "GET route that charges a user via payment API (Major Violation)",
        "code": """
@app.get("/pay/{user_id}")
def charge_user(user_id: str):
    stripe.charge(customer=user_id, amount=1000)
    return {"charged": True}
""",
        "expected_score": 0.0
    },

    {
        "id": "post_calls_payment_api",
        "description": "POST route that processes payment — correct usage",
        "code": """
@app.post("/payments/charge")
def charge(payload: ChargeSchema):
    result = stripe.charge(customer=payload.user_id, amount=payload.amount)
    return {"transaction_id": result.id}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_publishes_event",
        "description": "GET route that publishes to a message queue (Major Violation)",
        "code": """
@app.get("/trigger/{event}")
def trigger_event(event: str):
    queue.publish(topic="events", message=event)
    return {"triggered": True}
""",
        "expected_score": 0.0
    },

    {
        "id": "post_publishes_event",
        "description": "POST route that publishes to a message queue — correct",
        "code": """
@app.post("/events/publish")
def publish_event(event: EventSchema):
    queue.publish(topic="events", message=event.dict())
    return {"published": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "delete_calls_external_revoke",
        "description": "DELETE route that revokes an OAuth token via external API — correct",
        "code": """
@app.delete("/auth/tokens/{token_id}")
def revoke_token(token_id: str):
    oauth_client.revoke(token_id)
    db.tokens.delete_one({"id": token_id})
    return {"revoked": True}
""",
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 4 — Transaction / Session Blocks
    # DB transactions are still mutations — method must match.
    # =========================================================================

    {
        "id": "post_with_transaction",
        "description": "POST route using a DB transaction for atomic insert — correct",
        "code": """
@app.post("/transfer")
def transfer_funds(payload: TransferSchema):
    with db.start_session() as session:
        with session.start_transaction():
            db.accounts.update_one({"id": payload.from_id}, {"$inc": {"balance": -payload.amount}}, session=session)
            db.accounts.update_one({"id": payload.to_id}, {"$inc": {"balance": payload.amount}}, session=session)
    return {"transferred": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_with_transaction_mutation",
        "description": "GET route wrapping mutations in a transaction (Major Violation)",
        "code": """
@app.get("/settle/{id}")
def settle_account(id: str):
    with db.start_session() as session:
        with session.start_transaction():
            db.accounts.update_one({"id": id}, {"$set": {"settled": True}}, session=session)
    return {"done": True}
""",
        "expected_score": 0.0
    },

    {
        "id": "put_with_sqlalchemy_transaction",
        "description": "PUT route using SQLAlchemy transaction to update — correct",
        "code": """
@app.put("/invoices/{id}")
def update_invoice(id: str, data: InvoiceSchema):
    with session.begin():
        invoice = session.query(Invoice).filter_by(id=id).first()
        invoice.amount = data.amount
        invoice.status = data.status
    return {"updated": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_with_sqlalchemy_commit",
        "description": "GET route that commits a session (Ambiguous — side effect in GET)",
        "code": """
@app.get("/finalize/{id}")
def finalize(id: str):
    record = session.query(Record).filter_by(id=id).first()
    session.commit()
    return record
""",
        "expected_score": 0.5
    },

    {
        "id": "delete_with_transaction",
        "description": "DELETE route using transaction for cascading deletes — correct",
        "code": """
@app.delete("/users/{id}")
def delete_user_cascade(id: str):
    with db.start_session() as session:
        with session.start_transaction():
            db.orders.delete_many({"user_id": id}, session=session)
            db.users.delete_one({"id": id}, session=session)
    return {"deleted": True}
""",
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 5 — Framework Variety (Django, Express, Gin, Spring)
    # Same semantic rules, different syntax.
    # =========================================================================

    # --- Django ---
    {
        "id": "django_get_clean",
        "description": "Django GET view reading from ORM — correct",
        "code": """
class UserDetailView(APIView):
    def get(self, request, pk):
        user = User.objects.get(pk=pk)
        return Response(UserSerializer(user).data)
""",
        "expected_score": 1.0
    },

    {
        "id": "django_get_with_delete",
        "description": "Django GET view calling ORM .delete() (Major Violation)",
        "code": """
class UserDetailView(APIView):
    def get(self, request, pk):
        User.objects.filter(pk=pk).delete()
        return Response({"deleted": True})
""",
        "expected_score": 0.0
    },

    {
        "id": "django_post_create",
        "description": "Django POST view using serializer.save() to create — correct",
        "code": """
class UserCreateView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)
""",
        "expected_score": 1.0
    },

    {
        "id": "django_put_update",
        "description": "Django PUT view updating via ORM — correct",
        "code": """
class UserUpdateView(APIView):
    def put(self, request, pk):
        user = User.objects.get(pk=pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)
""",
        "expected_score": 1.0
    },

    {
        "id": "django_delete_read_only",
        "description": "Django DELETE view that only reads — misuse",
        "code": """
class UserDetailView(APIView):
    def delete(self, request, pk):
        user = User.objects.get(pk=pk)
        return Response({"email": user.email})
""",
        "expected_score": 0.6
    },

    # --- Express / Node.js ---
    {
        "id": "express_get_clean",
        "description": "Express GET handler with clean find — correct",
        "code": """
router.get("/products/:id", async (req, res) => {
    const product = await Product.findById(req.params.id);
    res.json(product);
});
""",
        "expected_score": 1.0
    },

    {
        "id": "express_get_with_save",
        "description": "Express GET handler calling .save() on a model (Major Violation)",
        "code": """
router.get("/views/:id", async (req, res) => {
    const post = await Post.findById(req.params.id);
    post.views += 1;
    await post.save();
    res.json(post);
});
""",
        "expected_score": 0.0
    },

    {
        "id": "express_post_create",
        "description": "Express POST handler creating a document — correct",
        "code": """
router.post("/products", async (req, res) => {
    const product = new Product(req.body);
    await product.save();
    res.status(201).json(product);
});
""",
        "expected_score": 1.0
    },

    {
        "id": "express_delete_correct",
        "description": "Express DELETE handler calling findByIdAndDelete — correct",
        "code": """
router.delete("/products/:id", async (req, res) => {
    await Product.findByIdAndDelete(req.params.id);
    res.json({ deleted: true });
});
""",
        "expected_score": 1.0
    },

    {
        "id": "express_put_read_only",
        "description": "Express PUT handler that only reads (Misuse)",
        "code": """
router.put("/users/:id/exists", async (req, res) => {
    const user = await User.findById(req.params.id);
    res.json({ exists: !!user });
});
""",
        "expected_score": 0.6
    },

    # --- Gin (Go) ---
    {
        "id": "gin_get_clean",
        "description": "Gin GET handler reading from DB — correct",
        "code": """
r.GET("/users/:id", func(c *gin.Context) {
    id := c.Param("id")
    var user User
    db.First(&user, id)
    c.JSON(200, user)
})
""",
        "expected_score": 1.0
    },

    {
        "id": "gin_get_with_delete",
        "description": "Gin GET handler calling db.Delete (Major Violation)",
        "code": """
r.GET("/remove/:id", func(c *gin.Context) {
    id := c.Param("id")
    db.Delete(&User{}, id)
    c.JSON(200, gin.H{"deleted": true})
})
""",
        "expected_score": 0.0
    },

    {
        "id": "gin_post_create",
        "description": "Gin POST handler creating a record — correct",
        "code": """
r.POST("/users", func(c *gin.Context) {
    var user User
    c.BindJSON(&user)
    db.Create(&user)
    c.JSON(201, user)
})
""",
        "expected_score": 1.0
    },

    # --- Spring Boot (Java) ---
    {
        "id": "spring_get_clean",
        "description": "Spring GET endpoint reading from repository — correct",
        "code": """
@GetMapping("/users/{id}")
public ResponseEntity<User> getUser(@PathVariable Long id) {
    return userRepository.findById(id)
        .map(ResponseEntity::ok)
        .orElse(ResponseEntity.notFound().build());
}
""",
        "expected_score": 1.0
    },

    {
        "id": "spring_get_with_save",
        "description": "Spring GET endpoint calling repository.save() (Major Violation)",
        "code": """
@GetMapping("/users/activate/{id}")
public ResponseEntity<User> activateUser(@PathVariable Long id) {
    User user = userRepository.findById(id).orElseThrow();
    user.setActive(true);
    userRepository.save(user);
    return ResponseEntity.ok(user);
}
""",
        "expected_score": 0.0
    },

    {
        "id": "spring_post_create",
        "description": "Spring POST endpoint saving a new entity — correct",
        "code": """
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    User user = new User(dto.getName(), dto.getEmail());
    userRepository.save(user);
    return ResponseEntity.status(201).body(user);
}
""",
        "expected_score": 1.0
    },

    {
        "id": "spring_delete_correct",
        "description": "Spring DELETE endpoint calling deleteById — correct",
        "code": """
@DeleteMapping("/users/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userRepository.deleteById(id);
    return ResponseEntity.noContent().build();
}
""",
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 6 — False Positive Traps
    # Mutation keywords appear in strings, comments, logs — NOT in operations.
    # Score must remain 1.0 for clean GET routes.
    # =========================================================================

    {
        "id": "fp_mutation_in_log",
        "description": "GET route with 'delete' only in a log message — no actual mutation",
        "code": """
@app.get("/status")
def get_status():
    logger.info("No delete operations were triggered")
    return {"status": "ok"}
""",
        "expected_score": 1.0
    },

    {
        "id": "fp_mutation_in_variable_name",
        "description": "GET route with a variable named 'update_time' — not a mutation",
        "code": """
@app.get("/report")
def get_report():
    update_time = datetime.now().isoformat()
    data = db.reports.find_one({})
    return {"data": data, "generated_at": update_time}
""",
        "expected_score": 1.0
    },

    {
        "id": "fp_insert_in_comment",
        "description": "GET route with 'insert' only in a comment — no actual mutation",
        "code": """
@app.get("/config")
def get_config():
    # We do NOT insert anything here, just read
    config = db.config.find_one({"active": True})
    return config
""",
        "expected_score": 1.0
    },

    {
        "id": "fp_save_in_string_response",
        "description": "GET route returning string containing 'save' — not a mutation",
        "code": """
@app.get("/help")
def get_help():
    return {"message": "Use POST /items to save a new item"}
""",
        "expected_score": 1.0
    },

    {
        "id": "fp_delete_in_docstring",
        "description": "DELETE keyword only in docstring of a GET route — no actual delete",
        "code": """
@app.get("/archive/{id}")
def get_archive(id: str):
    \"\"\"
    Returns archived item. Does NOT delete the item.
    To delete, use DELETE /archive/{id}
    \"\"\"
    item = db.archive.find_one({"id": id})
    return item
""",
        "expected_score": 1.0
    },

    {
        "id": "fp_update_as_field_name",
        "description": "GET route reading a field literally named 'last_update' — not a mutation",
        "code": """
@app.get("/meta/{id}")
def get_metadata(id: str):
    meta = db.meta.find_one({"id": id})
    return {"last_update": meta["last_update"], "version": meta["version"]}
""",
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 7 — Mixed / Compound Scenarios
    # Routes that conditionally mutate, or mix reads and writes.
    # =========================================================================

    {
        "id": "post_upsert",
        "description": "POST route doing an upsert (insert or update) — acceptable for POST",
        "code": """
@app.post("/settings")
def upsert_settings(payload: SettingsSchema):
    db.settings.update_one(
        {"user_id": payload.user_id},
        {"$set": payload.dict()},
        upsert=True
    )
    return {"saved": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_conditional_mutation",
        "description": "GET route that conditionally creates a record if not found (Ambiguous)",
        "code": """
@app.get("/profile/{id}")
def get_or_create_profile(id: str):
    profile = db.profiles.find_one({"id": id})
    if not profile:
        db.profiles.insert_one({"id": id, "created_at": now()})
        profile = db.profiles.find_one({"id": id})
    return profile
""",
        "expected_score": 0.5
    },

    {
        "id": "post_read_heavy",
        "description": "POST used for a complex read-only aggregation query (Moderate Misuse)",
        "code": """
@app.post("/analytics/query")
def run_analytics(filters: AnalyticsFilterSchema):
    pipeline = [
        {"$match": filters.dict()},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}
    ]
    result = list(db.sales.aggregate(pipeline))
    return {"result": result}
""",
        "expected_score": 0.6
    },

    {
        "id": "delete_soft_delete",
        "description": "DELETE route that soft-deletes by setting a flag — semantically correct",
        "code": """
@app.delete("/posts/{id}")
def soft_delete_post(id: str):
    db.posts.update_one({"id": id}, {"$set": {"deleted": True, "deleted_at": now()}})
    return {"deleted": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "patch_multiple_fields",
        "description": "PATCH route updating multiple fields via $set — correct",
        "code": """
@app.patch("/users/{id}")
def partial_update_user(id: str, payload: UserPatchSchema):
    db.users.update_one({"id": id}, {"$set": payload.dict(exclude_unset=True)})
    return {"updated": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "put_read_only",
        "description": "PUT route that only fetches data without any mutation (Misuse)",
        "code": """
@app.put("/debug/user/{id}")
def debug_user(id: str):
    user = db.users.find_one({"id": id})
    return {"debug": user}
""",
        "expected_score": 0.6
    },

    {
        "id": "get_with_insert_on_miss",
        "description": "GET route that inserts a default record on cache miss (Ambiguous)",
        "code": """
@app.get("/cache/{key}")
def get_cached(key: str):
    cached = db.cache.find_one({"key": key})
    if not cached:
        db.cache.insert_one({"key": key, "value": None})
    return cached
""",
        "expected_score": 0.5
    },

    {
        "id": "post_idempotent_check_then_insert",
        "description": "POST route checking for duplicate before inserting — correct",
        "code": """
@app.post("/subscriptions")
def subscribe(payload: SubscriptionSchema):
    existing = db.subscriptions.find_one({"email": payload.email})
    if not existing:
        db.subscriptions.insert_one(payload.dict())
    return {"subscribed": True}
""",
        "expected_score": 1.0
    },

    {
        "id": "get_orm_lazy_load_only",
        "description": "GET route that lazy-loads a related object — read only, correct",
        "code": """
@app.get("/orders/{id}/items")
def get_order_items(id: str):
    order = session.query(Order).filter_by(id=id).first()
    items = order.items  # lazy load, no mutation
    return [i.to_dict() for i in items]
""",
        "expected_score": 1.0
    },

    {
        "id": "get_with_write_lock",
        "description": "GET route acquiring a write lock — side effect beyond reading (Ambiguous)",
        "code": """
@app.get("/resource/{id}")
def get_with_lock(id: str):
    with db.lock(id, mode="write"):
        resource = db.resources.find_one({"id": id})
    return resource
""",
        "expected_score": 0.5
    },

    {
        "id": "post_used_as_rpc_action",
        "description": "POST used as RPC-style action endpoint — acceptable for non-CRUD actions",
        "code": """
@app.post("/actions/recalculate-scores")
def recalculate_scores():
    users = db.users.find({})
    for user in users:
        new_score = compute_score(user)
        db.users.update_one({"id": user["id"]}, {"$set": {"score": new_score}})
    return {"recalculated": True}
""",
        "expected_score": 1.0
    },
]