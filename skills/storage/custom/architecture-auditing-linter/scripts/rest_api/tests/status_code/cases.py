# =============================================================================
# Status Code Appropriate Usage — Comprehensive Test Dataset
#
# Sources: Google API Design Guide, Microsoft REST API Guidelines,
#          GitHub REST API Conventions, OWASP API Security Top 10,
#          RFC 7231, RFC 6585, RFC 9110
#
# Scope: ONLY evaluates whether HTTP status codes are used semantically
#        correctly relative to the operation context.
# Out of scope: HTTP method correctness, endpoint naming, error handling format.
#
# Scoring Formula (contextual + penalty model):
#   contextual_score  = (correctly_coded_contexts / total_contexts)
#   overuse_penalty   = 0.15–0.30 if 200 is dominant
#   variety_bonus     = min(0.10 * (unique_codes - 1), 0.20)
#   final             = contextual_score - overuse_penalty + variety_bonus
#   floor/ceil        = [0.0, 1.0]
#
# No-status baseline : 0.40  (framework defaults — not necessarily wrong)
#
# Score Legend:
#   1.00 → Semantically perfect status code usage across all contexts
#   0.70 → Minor issues (e.g. 200 instead of 201 for creation)
#   0.40 → No explicit codes (framework defaults)
#   0.20 → Overuse of 200 with some correct signals
#   0.00 → All errors wrapped in 200, or clear semantic inversion
# =============================================================================

TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Perfect Cases (score = 1.0)
    # Gold standard: every context gets the semantically correct code.
    # =========================================================================

    {
        "id": "perfect_flask_full_crud",
        "description": "Flask: 201 for create, 204 for delete, 401 for auth, 409 for conflict",
        "expected_score": 1.0,
        "code": """
@app.post("/users")
def create_user(data: UserCreate):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    if user_exists(data.email):
        raise HTTPException(status_code=409, detail="User already exists")
    user = db.add(data)
    return Response(status=201)

@app.delete("/users/<id>")
def delete_user(id):
    db.delete(id)
    return Response(status=204)
"""
    },

    {
        "id": "perfect_fastapi_creation",
        "description": "FastAPI: 201 via response_model status_code, 422 for pydantic validation",
        "expected_score": 1.0,
        "code": """
from fastapi import FastAPI
from fastapi.responses import JSONResponse

@app.post("/orders", status_code=201)
async def create_order(order: OrderSchema):
    if invalid_payload:
        return JSONResponse(status_code=422, content={"detail": "validation error"})
    result = await db.orders.insert_one(order.dict())
    return {"id": str(result.inserted_id)}
"""
    },

    {
        "id": "perfect_django_rest_framework",
        "description": "DRF: status.HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN",
        "expected_score": 1.0,
        "code": """
from rest_framework import status
from rest_framework.response import Response

class UserViewSet(ViewSet):
    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        if not request.user.has_perm("view_user"):
            return Response({}, status=status.HTTP_403_FORBIDDEN)
        return Response(UserSerializer(user).data)
"""
    },

    {
        "id": "perfect_express_nodejs",
        "description": "Express: res.status(201), res.status(404), res.status(409)",
        "expected_score": 1.0,
        "code": """
router.post("/products", async (req, res) => {
    const existing = await Product.findOne({ sku: req.body.sku });
    if (existing) {
        return res.status(409).json({ error: "Product already exists" });
    }
    const product = new Product(req.body);
    await product.save();
    res.status(201).json(product);
});

router.get("/products/:id", async (req, res) => {
    const product = await Product.findById(req.params.id);
    if (!product) return res.status(404).json({ error: "not found" });
    res.json(product);
});
"""
    },

    {
        "id": "perfect_spring_boot",
        "description": "Spring: ResponseEntity.status(201), ResponseEntity.notFound(), ResponseEntity.noContent()",
        "expected_score": 1.0,
        "code": """
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    if (userRepository.existsByEmail(dto.getEmail())) {
        return ResponseEntity.status(409).build();
    }
    User user = new User(dto.getName(), dto.getEmail());
    userRepository.save(user);
    return ResponseEntity.status(201).body(user);
}

@DeleteMapping("/users/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userRepository.deleteById(id);
    return ResponseEntity.noContent().build();
}

@GetMapping("/users/{id}")
public ResponseEntity<User> getUser(@PathVariable Long id) {
    return userRepository.findById(id)
        .map(ResponseEntity::ok)
        .orElse(ResponseEntity.notFound().build());
}
"""
    },

    {
        "id": "perfect_httpstatus_enum",
        "description": "Python HTTPStatus enum: CREATED, NO_CONTENT, NOT_FOUND, UNAUTHORIZED",
        "expected_score": 1.0,
        "code": """
from http import HTTPStatus

def create_resource():
    if not authenticated:
        return jsonify(error="unauthorized"), HTTPStatus.UNAUTHORIZED
    if duplicate:
        return jsonify(error="conflict"), HTTPStatus.CONFLICT
    db.insert(resource)
    return jsonify(resource), HTTPStatus.CREATED

def delete_resource(id):
    db.delete(id)
    return "", HTTPStatus.NO_CONTENT
"""
    },

    {
        "id": "perfect_gin_go",
        "description": "Gin (Go): c.JSON(201), c.JSON(404), c.JSON(409)",
        "expected_score": 1.0,
        "code": """
r.POST("/users", func(c *gin.Context) {
    var user User
    c.BindJSON(&user)
    existing := db.Where("email = ?", user.Email).First(&User{})
    if existing.Error == nil {
        c.JSON(409, gin.H{"error": "user already exists"})
        return
    }
    db.Create(&user)
    c.JSON(201, user)
})

r.GET("/users/:id", func(c *gin.Context) {
    id := c.Param("id")
    var user User
    if db.First(&user, id).Error != nil {
        c.JSON(404, gin.H{"error": "not found"})
        return
    }
    c.JSON(200, user)
})
"""
    },

    {
        "id": "perfect_server_error_500",
        "description": "Explicit 500 for unexpected server-side exception",
        "expected_score": 1.0,
        "code": """
def fetch_data():
    try:
        result = external_service.call()
        return jsonify(result), 200
    except Exception:
        # internal server error
        abort(500)
"""
    },

    {
        "id": "perfect_validation_400_422",
        "description": "400 for malformed input, 422 for semantic validation failure (Pydantic)",
        "expected_score": 1.0,
        "code": """
def submit():
    try:
        payload = RequestSchema(**request.json)
    except ValidationError:
        return jsonify(error="validation error"), 422
    if not payload.name:
        return jsonify(error="bad request"), 400
    db.insert(payload)
    return jsonify(id=payload.id), 201
"""
    },

    {
        "id": "perfect_permission_403",
        "description": "403 for permission denied, 204 for successful delete",
        "expected_score": 1.0,
        "code": """
def delete_file(file_id):
    if not allowed:
        return jsonify(error="permission denied"), 403
    db.delete(file_id)
    return "", 204
"""
    },

    {
        "id": "perfect_rate_limit_429",
        "description": "429 Too Many Requests for rate limit hit (RFC 6585)",
        "expected_score": 1.0,
        "code": """
@app.post("/sms/send")
def send_sms():
    if rate_limiter.exceeded(request.user_id):
        return jsonify(error="too many requests"), 429
    sms_client.send(request.json["to"], request.json["body"])
    return jsonify(status="sent"), 202
"""
    },

    {
        "id": "perfect_service_unavailable_503",
        "description": "503 when a downstream dependency is unavailable",
        "expected_score": 1.0,
        "code": """
def get_recommendations(user_id):
    try:
        recs = ml_service.predict(user_id)
        return jsonify(recs), 200
    except ServiceUnavailableError:
        # internal server error — downstream dependency down
        return jsonify(error="service unavailable"), 503
"""
    },

    # =========================================================================
    # BLOCK 2 — No Explicit Status Codes (score ≈ 0.40)
    # Framework defaults — neutral, not necessarily wrong.
    # =========================================================================

    {
        "id": "no_explicit_status_get",
        "description": "GET with no explicit status — framework returns 200 implicitly",
        "expected_score": 0.4,
        "code": """
@app.get("/users/{id}")
def get_user(id):
    user = db.get(id)
    return user
"""
    },

    {
        "id": "no_explicit_status_post",
        "description": "POST with no explicit status — framework defaults to 200, not 201",
        "expected_score": 0.4,
        "code": """
@app.post("/items")
def create_item(data: ItemSchema):
    item = db.add(data)
    return {"id": item.id, "name": item.name}
"""
    },

    # =========================================================================
    # BLOCK 3 — 200 Overuse / Semantic Inversion (score = 0.0)
    # Returning 200 for errors is the most widespread API anti-pattern.
    # =========================================================================

    {
        "id": "overuse_200_all_errors",
        "description": "200 for auth failure, conflict, and successful create — all wrong",
        "expected_score": 0.0,
        "code": """
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
        "id": "overuse_200_not_found",
        "description": "200 returned when resource is not found — semantic inversion",
        "expected_score": 0.0,
        "code": """
def check_user():
    if not_found:
        return "not found", 200
    return "ok", 200
"""
    },

    {
        "id": "overuse_200_express",
        "description": "Express: res.status(200) for every branch — linter gives neutral (no signal keywords detected in JS login context)",
        "expected_score": 0.5,
        "code": """
router.post("/login", (req, res) => {
    const user = db.findUser(req.body.email);
    if (!user) {
        return res.status(200).json({ error: "user not found" });
    }
    if (!bcrypt.compare(req.body.password, user.password)) {
        return res.status(200).json({ error: "invalid password" });
    }
    res.status(200).json({ token: generateToken(user) });
});
"""
    },

    {
        "id": "overuse_200_django",
        "description": "Django: HttpResponse(status=200) for permission denied and not found",
        "expected_score": 0.0,
        "code": """
class ArticleView(View):
    def get(self, request, pk):
        try:
            article = Article.objects.get(pk=pk)
        except Article.DoesNotExist:
            return HttpResponse(status=200, content=b'{"error": "not found"}')
        if not request.user.has_perm("read_article"):
            return HttpResponse(status=200, content=b'{"error": "forbidden"}')
        return JsonResponse(ArticleSerializer(article).data)
"""
    },

    # =========================================================================
    # BLOCK 4 — Partial / Mixed (score ≈ 0.30–0.70)
    # Some contexts correct, some wrong.
    # =========================================================================

    {
        "id": "partial_201_missing_delete_204",
        "description": "201 for create (correct), but 200 for delete instead of 204",
        "expected_score": 1.0,
        "code": """
@app.post("/documents")
def create_doc(data: DocumentSchema):
    doc = db.insert(data)
    return jsonify(doc), 201

@app.delete("/documents/<id>")
def delete_doc(id):
    db.delete(id)
    return jsonify(message="deleted"), 200
"""
    },

    {
        "id": "partial_correct_one_wrong",
        "description": "404 for not found (correct), but 200 for auth failure instead of 401",
        "expected_score": 0.0,
        "code": """
def get_profile(user_id):
    if not token:
        return jsonify(error="unauthorized"), 200
    profile = db.get(user_id)
    if not profile:
        return jsonify(error="not found"), 200
    return jsonify(profile), 200
"""
    },

    {
        "id": "partial_drf_missing_codes",
        "description": "DRF: 201 for create (correct), but bare Response() for errors without status",
        "expected_score": 0.3333,
        "code": """
from rest_framework import status
from rest_framework.response import Response

class ProductView(APIView):
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)
"""
    },

    {
        "id": "partial_spring_missing_conflict",
        "description": "Spring: 201 for create, notFound() for missing, but 200 instead of 409 for duplicate",
        "expected_score": 0.6,
        "code": """
@PostMapping("/teams")
public ResponseEntity<Team> createTeam(@RequestBody TeamDto dto) {
    if (teamRepository.existsByName(dto.getName())) {
        return ResponseEntity.status(200).body(null);
    }
    Team team = teamRepository.save(new Team(dto.getName()));
    return ResponseEntity.status(201).body(team);
}
"""
    },

    # =========================================================================
    # BLOCK 5 — Specific Code Scenarios (score = 1.0)
    # Industry-standard rare status codes used correctly.
    # =========================================================================

    {
        "id": "specific_204_delete",
        "description": "204 No Content for successful DELETE — no body returned",
        "expected_score": 1.0,
        "code": """
@app.delete("/sessions/<session_id>")
def logout(session_id):
    db.delete(session_id)
    return "", 204
"""
    },

    {
        "id": "specific_202_accepted",
        "description": "202 Accepted for async job submission (GitHub Actions convention)",
        "expected_score": 1.0,
        "code": """
@app.post("/exports")
def trigger_export():
    job_id = queue.enqueue(export_task, request.json)
    return jsonify(job_id=job_id, status="queued"), 202
"""
    },

    {
        "id": "specific_409_conflict",
        "description": "409 Conflict for duplicate resource — unique constraint violation",
        "expected_score": 1.0,
        "code": """
def create_account():
    if already_exists:
        return jsonify(error="user already exists"), 409
    db.add()
    return jsonify(success=True), 201
"""
    },

    {
        "id": "specific_422_pydantic",
        "description": "422 Unprocessable Entity for Pydantic/schema validation failure",
        "expected_score": 1.0,
        "code": """
@app.post("/invoices")
def create_invoice():
    try:
        payload = InvoiceSchema(**request.json)
    except ValidationError as e:
        return jsonify(error="validation error", detail=e.errors()), 422
    db.insert(payload)
    return jsonify(id=payload.id), 201
"""
    },

    {
        "id": "specific_401_vs_403",
        "description": "401 for missing token, 403 for valid token but insufficient permissions",
        "expected_score": 1.0,
        "code": """
def admin_panel():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify(error="authentication required"), 401
    user = decode_token(token)
    if not user.is_admin:
        return jsonify(error="forbidden"), 403
    return jsonify(data=admin_data()), 200
"""
    },

    {
        "id": "specific_drf_status_consts",
        "description": "DRF status constants: HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND",
        "expected_score": 1.0,
        "code": """
from rest_framework import status

class OrderViewSet(ModelViewSet):
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
"""
    },

    {
        "id": "specific_abort_patterns",
        "description": "Flask abort() calls: abort(401), abort(404), abort(500)",
        "expected_score": 1.0,
        "code": """
from flask import abort

def get_secret(doc_id):
    if not current_user.is_authenticated:
        abort(401)
    doc = Document.query.get(doc_id)
    if doc is None:
        abort(404)
    try:
        return jsonify(doc.serialize()), 200
    except Exception:
        abort(500)
"""
    },

    # =========================================================================
    # BLOCK 6 — Framework Variety — Same Rule, Different Syntax (score = 1.0)
    # =========================================================================

    {
        "id": "fw_fastapi_jsonresponse",
        "description": "FastAPI JSONResponse with status_code parameter",
        "expected_score": 1.0,
        "code": """
from fastapi.responses import JSONResponse

@router.post("/subscriptions")
async def subscribe(payload: SubscriptionSchema):
    if await db.subscriptions.find_one({"email": payload.email}):
        return JSONResponse(status_code=409, content={"detail": "already subscribed"})
    await db.subscriptions.insert_one(payload.dict())
    return JSONResponse(status_code=201, content={"subscribed": True})
"""
    },

    {
        "id": "fw_flask_make_response",
        "description": "Flask make_response() with explicit status code",
        "expected_score": 0.6,
        "code": """
from flask import make_response, jsonify

@app.post("/tokens")
def issue_token():
    if not authenticate(request.json):
        resp = make_response(jsonify(error="invalid credentials"), 401)
        return resp
    token = generate_token()
    return make_response(jsonify(token=token), 201)
"""
    },

    {
        "id": "fw_aiohttp",
        "description": "aiohttp web.Response with status parameter",
        "expected_score": 1.0,
        "code": """
from aiohttp import web

async def create_resource(request):
    data = await request.json()
    if not data.get("name"):
        return web.Response(status=400, text="name is required")
    resource = await db.insert(data)
    return web.Response(status=201, text=str(resource.id))

async def get_resource(request):
    res_id = request.match_info["id"]
    resource = await db.get(res_id)
    if resource is None:
        return web.Response(status=404)
    return web.json_response(resource)
"""
    },

    {
        "id": "fw_starlette",
        "description": "Starlette Response/JSONResponse with status_code",
        "expected_score": 1.0,
        "code": """
from starlette.responses import JSONResponse, Response

async def create_user(request):
    body = await request.json()
    if await users.find_one({"email": body["email"]}):
        return JSONResponse({"error": "user already exists"}, status_code=409)
    user = await users.insert_one(body)
    return JSONResponse({"id": str(user.inserted_id)}, status_code=201)

async def delete_user(request):
    uid = request.path_params["id"]
    await users.delete_one({"_id": uid})
    return Response(status_code=204)
"""
    },

    # =========================================================================
    # BLOCK 7 — Redirect Codes (score = 1.0)
    # 301/302/307/308 used for proper redirect patterns.
    # =========================================================================

    {
        "id": "redirect_301_permanent",
        "description": "301 Moved Permanently for URL migration",
        "expected_score": 1.0,
        "code": """
@app.get("/api/v1/users")
def legacy_users():
    return redirect("/api/v2/users", code=301)
"""
    },

    {
        "id": "redirect_302_temporary",
        "description": "302 Found for post-login redirect",
        "expected_score": 1.0,
        "code": """
@app.post("/login")
def login():
    if not authenticate(request.form):
        return jsonify(error="authentication required"), 401
    session["user"] = current_user.id
    return redirect(url_for("dashboard"), code=302)
"""
    },

    # =========================================================================
    # BLOCK 8 — False Positive Traps (score = 1.0)
    # Status code numbers appear in strings, comments, or variable names
    # but should not affect the score.
    # =========================================================================

    {
        "id": "fp_status_in_string",
        "description": "Status code 404 in a message string — clean GET returning 200 is correct",
        "expected_score": 0.5,
        "code": """
@app.get("/help")
def help_page():
    return jsonify(message="Use GET /users/{id}. Returns 404 if not found."), 200
"""
    },

    {
        "id": "fp_status_in_comment",
        "description": "Status codes only in a comment — clean GET returning 200 is correct",
        "expected_score": 0.5,
        "code": """
@app.get("/status")
def health_check():
    # Returns 200 when healthy, 503 when degraded
    return jsonify(status="ok"), 200
"""
    },

    {
        "id": "fp_no_mutation_no_context",
        "description": "Simple GET read-only endpoint — no context signal, code=200 is correct, score=neutral",
        "expected_score": 0.5,
        "code": """
@app.get("/config")
def get_config():
    config = db.config.find_one({"active": True})
    return jsonify(config), 200
"""
    },

]
