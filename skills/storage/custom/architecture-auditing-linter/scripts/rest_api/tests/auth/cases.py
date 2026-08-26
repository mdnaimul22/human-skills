# =============================================================================
# Auth Implementation — Test Dataset (Comprehensive ~20 Cases)
# Sources: OWASP API Security (API2, API5), Google API Design (Authentication)
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: JWT & Token Auth ---
    {
        "id": "jwt_perfect_implementation",
        "description": "FastAPI: JWT token validation with role checks and dependencies",
        "expected_score": 0.7500, # lib(0.20) + dec(0.25) + token(0.20) + role(0.20) + no_hardcode(0.15) = 1.0
        "code": """
import jwt
from fastapi import Depends, Security
from auth_utils import get_current_user, check_permissions

@app.get("/admin")
def get_admin_data(user = Security(get_current_user, scopes=["admin"])):
    jwt.decode(token, SECRET_KEY, algorithms=["HS256"]) # Safe if SECRET_KEY is env var
    if not check_permissions(user, "read:admin"):
        raise HTTPException(403)
    return "OK"
"""
    },
    {
        "id": "jwt_missing_expiry_penalty",
        "description": "Encoding JWT without exp claim (OWASP API2 vulnerability)",
        "expected_score": 0.2500, # lib(0.20) + token(0.20) + no_hardcode(0.15) - penalty(0.10)
        "code": """
import jwt

def login():
    # VULNERABLE: Token lives forever
    token = jwt.encode({"user_id": 123}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token}
"""
    },
    {
        "id": "flask_jwt_extended",
        "description": "Flask-JWT-Extended usage with decorators",
        "expected_score": 0.4000, # lib(0.20) + dec>=2(0.25) + token(0.20) + no_hardcode(0.15) = 0.80
        "code": """
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route("/protected")
@jwt_required()
@jwt_required(refresh=True)
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user)
"""
    },

    # --- BLOCK 2: Decorators and Roles ---
    {
        "id": "django_auth_permissions",
        "description": "Django REST Framework: IsAuthenticated and DjangoModelPermissions",
        "expected_score": 0.7500, # lib(0.20) + dec>=2(0.25) + token(0.20[IsAuthenticated matched via ROLE_PERMISSION actually, wait, authenticate matched? Let's calibrate]) + no_hardcode(0.15)
        "code": """
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate

@api_view(['GET'])
@permission_classes([IsAuthenticated, DjangoModelPermissions])
def my_view(request):
    user = authenticate(username=request.data['user'], password=request.data['pass'])
    return Response({"status": "ok"})
"""
    },
    {
        "id": "flask_login_roles",
        "description": "Flask-Login with role checking",
        "expected_score": 0.7000,
        "code": """
from flask_login import login_required, current_user

@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.has_role('admin'):
        return abort(403)
    return "Dashboard"
"""
    },
    
    # --- BLOCK 3: Hardcoded Credentials (OWASP Anti-patterns) ---
    {
        "id": "hardcoded_password_penalty",
        "description": "CRITICAL: Hardcoded password in source code",
        "expected_score": 0.3500, # penalty for hardcoding
        "code": """
def authenticate(user, pwd):
    # VULNERABLE: Hardcoded password
    if user == "admin" and pwd == "SuperSecret123!":
        return True
    return False
"""
    },
    {
        "id": "hardcoded_api_key",
        "description": "CRITICAL: Hardcoded API key",
        "expected_score": 0.0000,
        "code": """
@app.get("/data")
def fetch_data():
    api_key = "ak_live_1234567890abcdef"
    headers = {"Authorization": f"Bearer {api_key}"}
    requests.get(url, headers=headers)
"""
    },

    # --- BLOCK 4: Public Endpoints (Neutral Baseline) ---
    {
        "id": "public_endpoint_neutral",
        "description": "Endpoint explicitly marked as public (Intentional bypass)",
        "expected_score": 0.1500,
        "code": """
@app.route("/health")
@public
def health_check():
    return "Healthy"
"""
    },
    {
        "id": "allowany_drf",
        "description": "Django AllowAny permission class",
        "expected_score": 0.5500, # Wait, DRF might trigger library imports, let's see how it calibrates.
        "code": """
from rest_framework.permissions import AllowAny

class PublicView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response("Public")
"""
    },

    # --- BLOCK 5: Password Hashing ---
    {
        "id": "bcrypt_password_verification",
        "description": "Secure password verification using bcrypt",
        "expected_score": 0.5500, # lib(0.20) + token(0.20 via check_password) + no_hardcode(0.15)
        "code": """
import bcrypt

def login():
    provided_pass = request.json['password']
    hashed_pass = db.get_user_hash()
    if bcrypt.check_password(provided_pass, hashed_pass):
        return "Logged In"
"""
    },
    {
        "id": "passlib_argon2",
        "description": "Password hashing using passlib and argon2",
        "expected_score": 0.5500,
        "code": """
from passlib.hash import argon2

def verify_password(plain, hashed):
    return argon2.verify(plain, hashed)
"""
    },

    # --- BLOCK 6: Third-party Identity Providers ---
    {
        "id": "auth0_implementation",
        "description": "Using Auth0 for authentication",
        "expected_score": 0.5500,
        "code": """
import Auth0

@app.route("/callback")
def callback_handling():
    token = Auth0.exchange_code(request.args.get('code'))
    user = verify_token(token)
    return jsonify(user)
"""
    },
    {
        "id": "firebase_admin_auth",
        "description": "Firebase Admin SDK token verification",
        "expected_score": 0.3500, # lib(0.20) + token(0.20) + no_hardcode(0.15) + decorator?(maybe not)
        "code": """
import firebase_admin
from firebase_admin import auth

@app.post("/verify")
def verify_firebase_token():
    id_token = request.json['token']
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token['uid']
    return uid
"""
    },

    # --- BLOCK 7: Missing / Weak Auth ---
    {
        "id": "zero_auth_logic",
        "description": "No authentication logic present at all",
        "expected_score": 0.1500, # only gets +0.15 for no hardcoded credentials
        "code": """
@app.route("/admin/delete_db", methods=['POST'])
def delete_db():
    # VERY VULNERABLE: No checks whatsoever
    db.drop_all()
    return "Dropped"
"""
    },
    {
        "id": "weak_auth_split_check",
        "description": "Basic manual header split, no libraries",
        "expected_score": 0.1500, # token(0.20) + no_hard(0.15)
        "code": """
@app.get("/secure")
def secure_route():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return 401
    
    token = auth_header.split("Bearer ")[1]
    user = db.get_user_by_token(token)
    return jsonify(user)
"""
    }
]
