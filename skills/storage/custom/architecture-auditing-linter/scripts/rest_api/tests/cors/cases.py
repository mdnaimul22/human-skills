# =============================================================================
# CORS Implementation — Test Dataset
#
# Sources:
#   - Google API Design Guide (security policies)
#   - Microsoft REST API Guidelines §CORS
#   - GitHub REST API conventions (origin whitelisting)
#   - OWASP CORS Cheat Sheet (wildcard + credentials = critical violation)
#   - RFC 6454 (Origin), W3C CORS specification
#
# Scoring model (additive, max 1.0):
#   0.30 — Explicit origin whitelist
#   0.25 — Credentials mode handled correctly
#   0.20 — Allowed methods restricted (not wildcard)
#   0.15 — Allowed headers declared explicitly
#   0.10 — Preflight (OPTIONS) handled
#
# Penalty:
#   Wildcard origin (*) + credentials=True → 0.0  (OWASP critical violation)
#   No CORS config at all                  → 0.0
# =============================================================================

TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Perfect CORS (score = 1.0)
    # Explicit whitelist, credentials, restricted methods/headers, preflight.
    # =========================================================================

    {
        "id": "perfect_fastapi_cors",
        "description": "FastAPI CORSMiddleware: explicit origins, credentials, methods, headers, preflight",
        "expected_score": 1.0,
        "code": """
from fastapi.middleware.cors import CORSMiddleware
origins = ["https://app.example.com", "https://admin.example.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.options("*", cors())
""",
    },

    {
        "id": "perfect_flask_cors",
        "description": "Flask-CORS: origins whitelist, supports_credentials, headers, preflight",
        "expected_score": 1.0,
        "code": """
from flask_cors import CORS
CORS(
    app,
    origins=["https://app.example.com"],
    supports_credentials=True,
    allow_headers=["Authorization", "Content-Type"],
    methods=["GET", "POST", "DELETE", "OPTIONS"],
)
app.options("*", cors())
""",
    },

    {
        "id": "perfect_express_cors",
        "description": "Express cors(): origin whitelist function, credentials, preflight route",
        "expected_score": 1.0,
        "code": """
const cors = require('cors');
const allowedOrigins = ['https://app.example.com', 'https://beta.example.com'];
app.use(cors({
    origin: (origin, callback) => {
        if (allowedOrigins.includes(origin)) callback(null, true);
        else callback(new Error('CORS not allowed'));
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Authorization', 'Content-Type'],
}));
app.options('*', cors());
""",
    },

    {
        "id": "perfect_spring_cors",
        "description": "Spring @CrossOrigin: explicit origins, allowCredentials, methods, headers",
        "expected_score": 1.0,
        "code": """
@CrossOrigin(
    origins = {"https://app.example.com"},
    allowedHeaders = {"Authorization", "Content-Type"},
    methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.OPTIONS},
    allowCredentials = "true"
)
@RestController
public class UserController {}
""",
    },

    {
        "id": "perfect_gin_cors",
        "description": "Gin cors.Config: AllowOrigins list, AllowCredentials, methods, headers",
        "expected_score": 1.0,
        "code": """
import "github.com/gin-contrib/cors"
r.Use(cors.New(cors.Config{
    AllowOrigins:     []string{"https://app.example.com"},
    AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
    AllowHeaders:     []string{"Authorization", "Content-Type"},
    AllowCredentials: true,
}))
""",
    },

    # =========================================================================
    # BLOCK 2 — Good but Missing Preflight (score = 0.9)
    # Whitelist + credentials + methods + headers — only preflight missing.
    # =========================================================================

    {
        "id": "good_fastapi_no_preflight",
        "description": "FastAPI: whitelist, credentials, methods, headers — but no OPTIONS route",
        "expected_score": 0.9,
        "code": """
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
""",
    },

    {
        "id": "good_express_no_preflight",
        "description": "Express: cors() with whitelist and credentials but no app.options(*)",
        "expected_score": 0.9,
        "code": """
const cors = require('cors');
app.use(cors({
    origin: ["https://app.example.com"],
    credentials: true,
    methods: ["GET", "POST", "PUT"],
    allowedHeaders: ["Authorization", "Content-Type"],
}));
""",
    },

    # =========================================================================
    # BLOCK 3 — Django CORS Settings (score = 0.8)
    # CORS_ALLOWED_ORIGINS + CORS_ALLOW_CREDENTIALS + CORS_ALLOW_HEADERS.
    # No preflight pattern detectable from settings alone.
    # =========================================================================

    {
        "id": "good_django_cors_settings",
        "description": "django-cors-headers: CORS_ALLOWED_ORIGINS, ALLOW_CREDENTIALS, headers",
        "expected_score": 0.8,
        "code": """
CORS_ALLOWED_ORIGINS = ["https://app.example.com", "https://admin.example.com"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["authorization", "content-type", "x-request-id"]
""",
    },

    # =========================================================================
    # BLOCK 4 — Wildcard Origin Without Credentials (score = 0.25)
    # Acceptable for public anonymous APIs. No credentials risk.
    # =========================================================================

    {
        "id": "wildcard_no_credentials",
        "description": "Wildcard origin with no credentials — acceptable for public read-only API",
        "expected_score": 0.5,
        "code": """
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
)
""",
    },

    {
        "id": "wildcard_django_all_origins",
        "description": "django-cors-headers: CORS_ALLOW_ALL_ORIGINS=True without credentials",
        "expected_score": 0.15,
        "code": """
CORS_ALLOW_ALL_ORIGINS = True
""",
    },

    # =========================================================================
    # BLOCK 5 — OWASP Critical Violation (score = 0.0)
    # Wildcard origin (*) + credentials=True — exploitable CSRF vector.
    # =========================================================================

    {
        "id": "critical_wildcard_with_credentials",
        "description": "OWASP CRITICAL: allow_origins=['*'] + allow_credentials=True → instant 0.0",
        "expected_score": 0.0,
        "code": """
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
""",
    },

    {
        "id": "critical_express_wildcard_creds",
        "description": "Express: Access-Control-Allow-Origin: * + Allow-Credentials: true",
        "expected_score": 0.0,
        "code": """
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Credentials', 'true');
    res.header('Access-Control-Allow-Headers', 'Authorization, Content-Type');
    next();
});
""",
    },

    # =========================================================================
    # BLOCK 6 — No CORS Configuration (score = 0.0)
    # Routes exist but no CORS middleware/headers — browser requests blocked.
    # =========================================================================

    {
        "id": "no_cors_flask",
        "description": "Flask: routes defined, no CORS middleware — browser cross-origin blocked",
        "expected_score": 0.0,
        "code": """
from flask import Flask, jsonify
app = Flask(__name__)

@app.get("/users")
def get_users():
    return jsonify(users=[])
""",
    },

    {
        "id": "no_cors_express",
        "description": "Express: no cors() middleware, no Access-Control headers",
        "expected_score": 0.0,
        "code": """
const express = require('express');
const app = express();

app.get('/orders', (req, res) => {
    res.json({ orders: [] });
});
""",
    },

]
