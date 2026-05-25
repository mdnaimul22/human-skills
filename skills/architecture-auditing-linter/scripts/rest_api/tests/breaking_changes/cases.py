# =============================================================================
# Breaking Change Risk — Test Dataset
# Sources: Stripe API Versioning, Google AIP-180 (Backwards Compatibility)
#
# Scoring (see breaking_changes.py for full formula):
#   Response model usage (Pydantic/dataclass/TypedDict/Serializer)  : +0.20
#   Optional field usage (>=3: +0.20, >=1: +0.10)                   : +0.20
#   Default values on fields (all defaulted: +0.15)                 : +0.15
#   Deprecation markers (@deprecated, Sunset headers)               : +0.15
#   Consistent error schema (structured detail dicts)               : +0.15
#   Status code consistency (<=1 override: +0.15)                   : +0.15
#   Penalty: mixing raw dicts + models                              : -0.15
#   Penalty: AST mixed return types                                 : -0.10
# =============================================================================

TEST_CASES = [

    # --- BLOCK 1: Perfect / Near-Perfect Contracts ---
    {
        "id": "pydantic_optional_deprecated",
        "description": "Pydantic model with Optional fields, defaults, deprecation, structured errors",
        # model(0.20) + opt>=3(0.20) + defaults partial(0.08) + deprec(0.15) + error(0.15) + status(0.15) - req_penalty(0.08 not full) = 0.85
        "expected_score": 0.85,
        "code": """
from pydantic import BaseModel, Field
from typing import Optional
from fastapi import HTTPException
import warnings

class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = Field(default=None)

@app.get("/users/{id}", response_model=UserResponse, deprecated=True)
async def get_user(id: int):
    warnings.warn("Use /v2/users instead", DeprecationWarning)
    user = db.get(id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "Not found", "code": "USER_NOT_FOUND"})
    return UserResponse(**user)
"""
    },
    {
        "id": "dataclass_all_optional",
        "description": "Dataclass response with all Optional fields and structured errors",
        # model(0.20) + opt>=3(0.20) + defaults(0) + no_deprec(0) + error(0.15) + status(0.15) = 0.70
        "expected_score": 0.70,
        "code": """
from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException

@dataclass
class ProductResponse:
    id: int
    name: str
    price: Optional[float] = None
    category: Optional[str] = None
    tags: Optional[list] = None

@app.get("/products/{id}")
async def get_product(id: int):
    product = db.get(id)
    if not product:
        raise HTTPException(status_code=404, detail={"message": "Product not found", "code": "NOT_FOUND"})
    return ProductResponse(**product)
"""
    },

    # --- BLOCK 2: Good But Missing Some Signals ---
    {
        "id": "model_no_deprecation",
        "description": "Pydantic model, Optional fields, but no deprecation markers",
        # model(0.20) + opt>=3(0.20) + defaults(0) + no_deprec(0) + error(0.15) + status(0.15) = 0.70
        "expected_score": 0.70,
        "code": """
from pydantic import BaseModel, Field
from typing import Optional
from fastapi import HTTPException

class OrderResponse(BaseModel):
    id: int
    status: str
    total: float
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    tracking_url: Optional[str] = Field(default=None)

@app.get("/orders/{id}", response_model=OrderResponse)
async def get_order(id: int):
    order = db.get(id)
    if not order:
        raise HTTPException(status_code=404, detail={"message": "Order not found"})
    return OrderResponse(**order)
"""
    },
    {
        "id": "model_no_optional",
        "description": "Pydantic model but all fields required — risky for evolution",
        # model(0.20) + no_opt(0) + no_defaults(0) + no_deprec(0) + error(0.15) + status(0.15) = 0.50
        "expected_score": 0.50,
        "code": """
from pydantic import BaseModel
from fastapi import HTTPException

class StrictResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str

@app.get("/contacts/{id}", response_model=StrictResponse)
async def get_contact(id: int):
    if not found:
        raise HTTPException(status_code=404, detail={"message": "Not found"})
    return StrictResponse(**data)
"""
    },

    # --- BLOCK 3: Raw Dict Returns (Unstable Contracts) ---
    {
        "id": "raw_dict_return",
        "description": "Returns raw dict — no contract, breaking changes invisible",
        # no_model(0) + no_opt(0) + no_defaults(0) + no_deprec(0) + error(0.15) + status(0.15) = 0.30
        "expected_score": 0.30,
        "code": """
from fastapi import HTTPException

@app.get("/users/{id}")
async def get_user(id: int):
    user = db.get(id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "Not found"})
    return {"id": user.id, "name": user.name, "email": user.email}
"""
    },
    {
        "id": "jsonify_raw_dict",
        "description": "Flask jsonify with raw dict — no model, abort error (unstructured)",
        # no_model(0) + no_opt(0) + no_defaults(0) + no_deprec(0) + error_unstructured(0.08) + status(0.15) = 0.23
        "expected_score": 0.23,
        "code": """
from flask import jsonify, abort

@app.route("/products/<int:id>")
def get_product(id):
    product = db.get(id)
    if not product:
        abort(404)
    return jsonify({"id": product.id, "name": product.name, "price": product.price})
"""
    },

    # --- BLOCK 4: Mixed Response Types (Most Dangerous) ---
    {
        "id": "mixed_dict_and_model",
        "description": "RISK: Returns dict in one path and model in another",
        # model(0.20) + opt1(0.10) + defaults(0) + no_deprec(0) + error_unstructured(0.08) + status(0.15) - mix_penalty(-0.15) = 0.38
        "expected_score": 0.38,
        "code": """
from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException

class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None

@app.get("/users/{id}")
async def get_user(id: int):
    user = db.get(id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    if user.is_admin:
        return {"id": user.id, "name": user.name, "role": "admin"}
    return UserResponse(**user.dict())
"""
    },

    # --- BLOCK 5: Required Fields Without Defaults ---
    {
        "id": "many_required_fields",
        "description": "Model with many required fields and no defaults — high breaking risk",
        # model(0.20) + no_opt(0) + no_defaults(0) + no_deprec(0) + error(0.15) + status(0.15) - mix(-.15) = 0.35
        "expected_score": 0.35,
        "code": """
from pydantic import BaseModel
from fastapi import HTTPException

class InvoiceCreate(BaseModel):
    customer_id: str
    amount: float
    currency: str
    due_date: str
    line_items: list
    tax_rate: float
    billing_address: dict

@app.post("/invoices")
async def create_invoice(data: InvoiceCreate):
    if not data.customer_id:
        raise HTTPException(status_code=400, detail={"message": "Customer required"})
    return {"id": "inv_123"}
"""
    },

    # --- BLOCK 6: With Deprecation Markers ---
    {
        "id": "deprecated_endpoint",
        "description": "Properly deprecated endpoint with sunset header",
        # no_model(0) + no_opt(0) + no_defaults(0) + deprec(0.15) + no_error(0) + status(0.15) = 0.30
        "expected_score": 0.30,
        "code": """
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.get("/legacy/users", deprecated=True)
async def get_legacy_users():
    # DEPRECATED: Use /v2/users instead
    users = db.list_all()
    response = JSONResponse(content={"users": users}, status_code=200)
    response.headers["Sunset"] = "2025-12-31"
    response.headers["Deprecation"] = "true"
    return response
"""
    },

    # --- BLOCK 7: Minimal / Empty Code ---
    {
        "id": "health_check_only",
        "description": "Simple health check — no models, no errors, no risk",
        # all 0 except status(0.15) = 0.15
        "expected_score": 0.15,
        "code": """
@app.get("/health")
def health():
    return {"status": "ok"}
"""
    },
    {
        "id": "zero_patterns",
        "description": "Code with absolutely no API patterns",
        # status(0.15) only
        "expected_score": 0.15,
        "code": """
def calculate(x, y):
    return x + y

result = calculate(1, 2)
"""
    },

    # --- BLOCK 8: Error Schema Consistency ---
    {
        "id": "inconsistent_errors",
        "description": "Multiple error responses with inconsistent shapes",
        # model(0.20) + no_opt(0) + no_defaults(0) + no_deprec(0) + error_unstructured(0.08) + multi_status(0) - mix(-0.15) = 0.13
        "expected_score": 0.13,
        "code": """
from pydantic import BaseModel
from fastapi import HTTPException

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.get("/items/{id}")
async def get_item(id: int):
    if id < 0:
        raise HTTPException(status_code=400, detail="Bad ID")
    if id == 0:
        raise HTTPException(status_code=404, detail="Not found")
    if id > 1000:
        raise HTTPException(status_code=403, detail="Forbidden")
    if id > 500:
        raise HTTPException(status_code=429, detail="Rate limited")
    return {"id": id, "name": "Widget", "price": 9.99}
"""
    },

    # --- BLOCK 9: Serializer Pattern (Django) ---
    {
        "id": "django_serializer",
        "description": "DRF serializer — structured response model",
        # model(0.20) + no_opt(0) + no_defaults(0) + no_deprec(0) + no_error(0) + status(0.15) = 0.35
        "expected_score": 0.35,
        "code": """
from rest_framework import serializers
from rest_framework.response import Response

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
"""
    },

    # --- BLOCK 10: TypedDict Pattern ---
    {
        "id": "typeddict_response",
        "description": "TypedDict response — structured but limited",
        # model(0.20) + no_opt(0) + no_defaults(0) + no_deprec(0) + error(0.15) + status(0.15) - mix(-0.15) = 0.35
        "expected_score": 0.35,
        "code": """
from typing import TypedDict
from fastapi import HTTPException

class UserDict(TypedDict):
    id: int
    name: str
    email: str

@app.get("/users/{id}")
async def get_user(id: int) -> UserDict:
    user = db.get(id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "Not found"})
    return {"id": user.id, "name": user.name, "email": user.email}
"""
    },
]
