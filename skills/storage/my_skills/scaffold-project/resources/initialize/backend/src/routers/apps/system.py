from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from src.apps.auth import Principal, decode_token_claims
from src.apps.system import SystemStatusSnapshot
from src.config import Settings, setup_logger
from src.schema import (
    LivenessResponse,
    LivenessStatus,
    ReadinessResponse,
    ReadinessStatus,
    RootMetadataResponse,
)
from src.services.apps.system import SystemService, get_system_service

logger = setup_logger(Settings.LOG_DIR / "router.log", name="routers.apps.system")
router = APIRouter(tags=["system"])


def _extract_token(request: Request, authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        tok = authorization[7:].strip()
        if tok:
            return tok
    cookie_tok = request.cookies.get("access_token")
    if cookie_tok:
        return cookie_tok[7:].strip() if cookie_tok.startswith("Bearer ") else cookie_tok.strip()
    query_tok = request.query_params.get("token")
    if query_tok:
        return query_tok[7:].strip() if query_tok.startswith("Bearer ") else query_tok.strip()
    return None


async def require_system_admin_access(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Principal:
    if Settings.is_development:
        return Principal(user_id="dev:local", tier="admin", scopes=frozenset({"admin", "*"}))

    client_host = request.client.host if request.client is not None else ""
    has_proxy_headers = (
        "x-forwarded-for" in request.headers
        or "x-real-ip" in request.headers
        or "forwarded" in request.headers
    )
    if client_host in ("127.0.0.1", "::1") and not has_proxy_headers:
        return Principal(user_id="system:localhost", tier="admin", scopes=frozenset({"admin", "*"}))

    token = _extract_token(request, authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    try:
        claims = decode_token_claims(token, expected_type="access")
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    is_admin = claims.tier == "admin" or "admin" in claims.scopes or "*" in claims.scopes
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    return Principal(
        user_id=claims.sub,
        id=claims.sub,
        tier=claims.tier,
        scopes=frozenset(claims.scopes),
        jti=claims.jti,
    )


@router.get("/", response_model=RootMetadataResponse)
async def root(
    service: SystemService = Depends(get_system_service),
) -> RootMetadataResponse:
    return service.get_root_metadata()


@router.api_route("/health", methods=["GET", "HEAD"], response_model=LivenessResponse)
async def health_liveness(
    response: Response,
    service: SystemService = Depends(get_system_service),
) -> LivenessResponse:
    result = service.get_liveness()
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    if result.status == LivenessStatus.SHUTTING_DOWN:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.api_route("/health/ready", methods=["GET", "HEAD"], response_model=ReadinessResponse)
async def health_readiness(
    response: Response,
    service: SystemService = Depends(get_system_service),
) -> ReadinessResponse:
    result = await service.evaluate_readiness(force_refresh=False)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    if result.status == ReadinessStatus.UNREADY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/system/status", response_model=SystemStatusSnapshot)
async def system_status(
    _admin: Principal = Depends(require_system_admin_access),
    service: SystemService = Depends(get_system_service),
) -> SystemStatusSnapshot:
    return await service.get_system_status(force_refresh=False)
