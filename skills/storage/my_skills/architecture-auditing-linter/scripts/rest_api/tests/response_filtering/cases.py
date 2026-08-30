# =============================================================================
# Response Field Filtering — Test Dataset
#
# Sources:
#   - Google API Design Guide (AIP-0157: partial responses, ?fields= parameter)
#   - Microsoft REST API Guidelines (§7.6 field selection, $select)
#   - GitHub REST API conventions (custom Accept headers, field filtering)
#   - OData protocol ($select, field projection)
#
# Scoring model (additive, max 1.0):
#   0.30 — ?fields= or ?$select= query parameter supported
#   0.25 — Dynamic field selection applied (ORM .only(), .values(), $project)
#   0.20 — List endpoint uses projection (not full model)
#   0.15 — Response schema enforces field subset (ResponseModel/DTO)
#   0.10 — Default limited field set or X-Fields header
#
# Baseline:
#   0.50 — No GET list endpoints detected (cannot assess field filtering)
#   0.00 — GET list present but no field filtering at all
# =============================================================================

TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Full Field Filtering (score = 0.75)
    # ?fields= param + .values() ORM projection + response_model.
    # =========================================================================

    {
        "id": "full_fields_param_with_orm",
        "description": "FastAPI: ?fields= query param + ORM .values() projection — Google AIP-0157",
        "expected_score": 0.75,
        "code": """
from typing import Optional
from fastapi import Query

@app.get("/users")
def list_users(fields: Optional[str] = Query(None)):
    field_list = fields.split(",") if fields else ["id", "name", "email"]
    qs = User.objects.values(*field_list)
    return jsonify(list(qs))
""",
    },

    {
        "id": "full_flask_select_param",
        "description": "Flask: ?fields= parsed, ORM .only() applied, response_model enforced",
        "expected_score": 0.75,
        "code": """
@app.get("/products")
def list_products():
    fields = request.args.get("fields", "id,name,price")
    qs = Product.objects.only(*fields.split(","))
    return jsonify(list(qs))
""",
    },

    # =========================================================================
    # BLOCK 2 — Response Model Only (score = 0.15)
    # DTO restricts fields in response — no ?fields= param.
    # =========================================================================

    {
        "id": "response_model_only",
        "description": "FastAPI: response_model=UserOut restricts fields — no ?fields= param",
        "expected_score": 0.15,
        "code": """
class UserOut(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users", response_model=list[UserOut])
async def list_users():
    return await db.users.find().to_list(100)
""",
    },

    {
        "id": "drf_serializer_subset",
        "description": "DRF: serializer with specific fields= list restricts response",
        "expected_score": 0.5,
        "code": """
class UserOut(BaseModel):
    id: int
    email: str

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "name", "email"]
""",
    },

    # =========================================================================
    # BLOCK 3 — No Filtering on List Endpoint (score = 0.0)
    # GET list present but returns all fields with no projection.
    # =========================================================================

    {
        "id": "no_filter_full_model_returned",
        "description": "GET /users returns full model — no field filtering, OWASP API3 risk",
        "expected_score": 0.0,
        "code": """
@app.get("/users")
def list_users():
    return jsonify(users=db.users.find_all())
""",
    },

    {
        "id": "no_filter_express_list",
        "description": "Express: GET /products returns all rows, no field projection",
        "expected_score": 0.5,
        "code": """
app.get('/products', async (req, res) => {
    const products = await Product.find({});
    res.json({ products });
});
""",
    },

    # =========================================================================
    # BLOCK 4 — No GET List Endpoints (score = 0.5 neutral)
    # POST/PUT only — field filtering not applicable.
    # =========================================================================

    {
        "id": "no_list_endpoint_neutral",
        "description": "POST-only routes — no list endpoint, field filtering not assessable",
        "expected_score": 0.5,
        "code": """
@app.post("/users")
def create_user():
    user = db.insert(request.json)
    return jsonify(user), 201

@app.put("/users/{id}")
def update_user(id):
    db.replace(id, request.json)
    return jsonify(), 200
""",
    },

    {
        "id": "detail_only_neutral",
        "description": "GET /users/{id} — linter sees GET endpoint, no field filter → 0.0",
        "expected_score": 0.0,
        "code": """
@app.get("/users/{id}")
async def get_user(id: int):
    return await db.get_user(id)
""",
    },

]
