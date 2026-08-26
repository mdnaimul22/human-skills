# =============================================================================
# Sensitive Data in Response — Test Dataset
#
# Sources:
#   - OWASP API Security Top 10 (API3:2023 — Broken Object Property Level Auth)
#   - Google API Design Guide (data minimization, field masks)
#   - Microsoft REST API Guidelines (response field selection)
#   - GitHub REST API conventions (lean response objects)
#
# Scoring model (start 1.0, deduct penalties):
#   -0.40 — Sensitive field (password/secret/token) in response serializer
#   -0.30 — fields = '__all__' — returns every DB column
#   -0.10 — SELECT * equivalent without projection
#
# Bonuses:
#   +0.20 — Explicit exclude= or write_only=True on sensitive fields
#   +0.15 — Separate response DTO/schema (not DB model exposed directly)
#   +0.10 — fields= / only= restricts returned fields
#
# Baseline:
#   0.50 — No serialization context detected (cannot assess)
# =============================================================================

TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Perfect Data Minimization (score = 1.0)
    # Explicit exclusion of sensitive fields + separate response DTO.
    # =========================================================================

    {
        "id": "perfect_exclude_and_dto",
        "description": "DRF: exclude=['password','secret'] + separate response DTO",
        "expected_score": 1.0,
        "code": """
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ["password", "secret", "api_key"]
""",
    },

    {
        "id": "perfect_fastapi_response_model",
        "description": "FastAPI: response_model=UserOut — only declared fields returned",
        "expected_score": 1.0,
        "code": """
class UserOut(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{id}", response_model=UserOut)
async def get_user(id: int):
    return await db.get_user(id)
""",
    },

    {
        "id": "perfect_marshmallow_fields_only",
        "description": "Marshmallow Schema: only=['id','name','email'] — restricts fields",
        "expected_score": 1.0,
        "code": """
class UserSchema(Schema):
    class Meta:
        fields = ["id", "name", "email"]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ["password"]
""",
    },

    # =========================================================================
    # BLOCK 2 — fields='__all__' Violation (score = 0.7)
    # Returns every DB column — no field selection applied.
    # =========================================================================

    {
        "id": "violation_fields_all",
        "description": "DRF: fields='__all__' — exposes every model column including password",
        "expected_score": 0.7,
        "code": """
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
""",
    },

    {
        "id": "violation_fields_all_with_model",
        "description": "Marshmallow: fields='__all__' — full model exposure",
        "expected_score": 0.95,
        "code": """
class UserSchema(ModelSchema):
    class Meta:
        fields = "__all__"
        model = User
""",
    },

    # =========================================================================
    # BLOCK 3 — No Serialization Context (score = 0.5 neutral)
    # No serializer or schema present — cannot assess exposure.
    # =========================================================================

    {
        "id": "no_serializer_context",
        "description": "Simple route returning dict — no serializer context to evaluate",
        "expected_score": 0.5,
        "code": """
@app.get("/config")
def get_config():
    return jsonify(config={"debug": False, "version": "1.0"})
""",
    },

    {
        "id": "no_serializer_fastapi",
        "description": "FastAPI route with no response_model or schema — neutral",
        "expected_score": 0.5,
        "code": """
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
""",
    },

    # =========================================================================
    # BLOCK 4 — Sensitive Field in Response Model (score varies)
    # Direct model serialization that includes sensitive fields.
    # =========================================================================

    {
        "id": "violation_password_in_schema",
        "description": "Schema includes password field — OWASP API3 violation",
        "expected_score": 1.0,
        "code": """
class UserSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    password = fields.Str()
    email = fields.Str()
""",
    },

    {
        "id": "violation_write_only_fixed",
        "description": "Password field marked write_only=True — correct mitigation",
        "expected_score": 1.0,
        "code": """
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        fields = ["id", "name", "email", "password"]
        exclude_fields = ["password"]
""",
    },

]
