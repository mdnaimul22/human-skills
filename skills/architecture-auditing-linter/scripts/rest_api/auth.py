import re
from typing import Any
from helpers.tool import Tool


# ── Auth signal patterns ──────────────────────────────────────────────────────

AUTH_LIBRARIES = re.compile(
    r'\b(jwt|PyJWT|python-jose|jose|authlib|flask_jwt|flask_login|'
    r'fastapi_users|django\.contrib\.auth|rest_framework\.permissions|'
    r'rest_framework\.authentication|OAuth|oauth2|Keycloak|Auth0|'
    r'Cognito|firebase_admin|passlib|bcrypt|argon2)\b',
    re.IGNORECASE,
)

AUTH_DECORATORS = re.compile(
    r'@(login_required|requires_auth|jwt_required|token_required|'
    r'permission_required|has_permission|authenticated|'
    r'Depends\(get_current_user\)|Depends\(verify_token\)|'
    r'Security\(|HTTPBearer|HTTPBasic|APIKeyHeader|OAuth2)',
    re.IGNORECASE,
)

TOKEN_VALIDATION = re.compile(
    r'\b(decode_token|verify_token|validate_token|jwt\.decode|'
    r'jwt\.verify|verify_jwt|check_token|bearer_token|'
    r'Authorization\.split|Bearer\s+token|get_current_user|'
    r'authenticate|is_authenticated|verify_password|check_password)\b',
    re.IGNORECASE,
)

ROLE_PERMISSION_CHECKS = re.compile(
    r'\b(has_role|has_permission|is_admin|is_staff|check_permissions|'
    r'role\s*==|permission\s*in|IsAdminUser|IsAuthenticated|'
    r'AllowAny|DjangoModelPermissions|scope|scopes|claims)\b',
    re.IGNORECASE,
)

# Bad patterns — auth smell
HARDCODED_CREDENTIALS = re.compile(
    r'(password\s*=\s*["\'][^"\']{3,}["\']'
    r'|secret\s*=\s*["\'][^"\']{3,}["\']'
    r'|api_key\s*=\s*["\'][^"\']{3,}["\']'
    r'|token\s*=\s*["\'][^"\']{3,}["\'])',
    re.IGNORECASE,
)

MISSING_EXPIRY = re.compile(
    r'jwt\.encode\b(?:(?!exp).)*\)',
    re.IGNORECASE | re.DOTALL,
)

# Public / no-auth markers (intentional bypass)
PUBLIC_ENDPOINT_SIGNALS = re.compile(
    r'@(public|AllowAny|no_auth|open_route|anonymous)',
    re.IGNORECASE,
)


class AuthImplementation(Tool):
    def __init__(self):
        super().__init__(
            name="auth_implementation",
            description=(
                "Scores authentication and authorisation implementation in REST API code: "
                "checks for auth libraries, decorator-based enforcement, token validation, "
                "role/permission checks, and absence of hardcoded credentials."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        score = 0.0
        suggestions = []

        # 1. Auth library imported (0.20)
        if AUTH_LIBRARIES.search(source_code):
            score += 0.20
        else:
            suggestions.append("Import and use a standard authentication library (e.g., PyJWT, Authlib, passlib) instead of rolling custom auth.")

        # 2. Auth decorators / dependency injection (0.25)
        decorator_count = len(AUTH_DECORATORS.findall(source_code))
        if decorator_count >= 2:
            score += 0.25
        elif decorator_count == 1:
            score += 0.15
            suggestions.append("Ensure all protected endpoints are secured with authentication decorators/dependencies (e.g. @login_required, Depends()).")
        else:
            suggestions.append("Use authentication decorators or dependency injection to secure your API endpoints globally or per-route.")

        # 3. Token validation logic present (0.20)
        if TOKEN_VALIDATION.search(source_code):
            score += 0.20
        else:
            suggestions.append("Include explicit token/session validation logic (e.g., jwt.decode, verify_token) to verify user identity.")

        # 4. Role / permission checks (authorisation layer) (0.20)
        if ROLE_PERMISSION_CHECKS.search(source_code):
            score += 0.20
        else:
            suggestions.append("Implement role-based or permission-based authorization checks (e.g., is_admin, has_permission) to control resource access.")

        # 5. No hardcoded credentials (0.15 bonus / penalty)
        hardcoded_count = len(HARDCODED_CREDENTIALS.findall(source_code))
        if hardcoded_count == 0:
            score += 0.15
        else:
            score -= 0.20 * hardcoded_count
            suggestions.append("CRITICAL: Remove hardcoded credentials (passwords, secrets, api_keys). Load them from secure environment variables (e.g. Settings).")

        # 6. Penalty if JWT used without exp claim
        if MISSING_EXPIRY.search(source_code):
            score -= 0.10
            suggestions.append("CRITICAL: When generating JWTs, always include an expiration ('exp') claim to prevent indefinite token validity.")

        # If code has only public endpoints, don't penalise missing auth
        all_public = bool(PUBLIC_ENDPOINT_SIGNALS.search(source_code)) and score == 0.0
        if all_public:
            return 0.5, ["Endpoints appear to be public by design. Ensure sensitive routes are not exposed."]

        return round(min(max(score, 0.0), 1.0), 4), suggestions