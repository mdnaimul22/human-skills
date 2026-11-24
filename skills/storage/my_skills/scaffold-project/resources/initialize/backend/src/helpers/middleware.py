import hashlib
import time
import uuid

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
from src.config import request_id_ctx, set_telemetry, reset_telemetry
from src.apps.waf import WAFManager


def _extract_client_ip(request: Request) -> str:
    raw_ip = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For")
    )
    if raw_ip:
        return raw_ip.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_waf_guard(
    waf: WAFManager,
    client_ip: str,
    path: str,
    query: str,
    headers: dict[str, str],
    method: str,
    logger,
    request_id: str,
) -> PlainTextResponse | None:
    result = await waf.inspect(client_ip, path, query, headers, method)
    if result.decision == "rate_limit":
        logger.warning(f"⚠️ RATE LIMITED IP {client_ip} on {path}")
        await waf.track_url(path, 429)
        return PlainTextResponse(
            "Too Many Requests - Rate Limit Exceeded.",
            status_code=429,
            headers={"X-Request-ID": request_id, "Retry-After": "60"},
        )
    if result.decision == "block":
        logger.warning(f"🚫 BLOCKED IP {client_ip} on {path} (reason: {result.reason})")
        await waf.track_url(path, 403)
        return PlainTextResponse(
            "Forbidden - Access Denied.",
            status_code=403,
            headers={"X-Request-ID": request_id},
        )
    return None


def _apply_security_headers(response: Response, request_id: str, latency_ms: float, settings) -> None:
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"


def _log_request(logger, client_ip: str, method: str, path: str, status_code: int, latency_ms: float) -> None:
    logger.info(
        f"{client_ip} - {method} {path} → {status_code} ({latency_ms:.1f}ms)",
        extra={
            "duration_ms": round(latency_ms, 3), "http_status": status_code,
            "method": method, "endpoint": path, "client_ip": client_ip,
        },
    )


def register_middleware(app, logger, settings) -> None:
    @app.middleware("http")
    async def request_lifecycle(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:8]
        request.state.request_id = request_id
        client_ip = _extract_client_ip(request)
        request.state.client_ip = client_ip
        guest_id = request.headers.get("X-Guest-ID") or request.cookies.get("guest_id")
        if not guest_id:
            ua = request.headers.get("User-Agent") or ""
            guest_id = "gst_" + hashlib.sha256(f"{client_ip}:{ua}".encode()).hexdigest()[:16]
        request.state.guest_id = guest_id
        request.state.user_id = None
        request.state.job_id = None
        path = request.url.path
        parts = [p for p in path.strip("/").split("/") if p and p not in ("api", "v1")]
        derived_service = ".".join(parts[:2]) if parts else "root"
        request.state.service = derived_service

        token = request_id_ctx.set(request_id)
        ctx_token = set_telemetry(
            request_id=request_id,
            client_ip=client_ip,
            guest_id=guest_id,
            endpoint=path,
            service=derived_service,
            method=request.method,
        )
        try:
            waf = WAFManager()
            blocked_response = await _check_waf_guard(
                waf, client_ip, path, request.url.query,
                dict(request.headers), request.method, logger, request_id
            )
            if blocked_response is not None:
                return blocked_response

            start = time.perf_counter()
            try:
                response: Response = await call_next(request)
            except Exception:
                latency_ms = (time.perf_counter() - start) * 1000.0
                state_user = request.state.user_id
                state_job = request.state.job_id
                state_svc = request.state.service
                set_telemetry(
                    status_code=500,
                    user_id=state_user,
                    job_id=state_job,
                    service=state_svc,
                )
                logger.info(
                    f"{client_ip} - {request.method} {path} → 500 ({latency_ms:.1f}ms)",
                    extra={
                        "duration_ms": round(latency_ms, 3), "http_status": 500,
                        "method": request.method, "endpoint": path,
                        "client_ip": client_ip,
                    },
                )
                raise
            else:
                latency_ms = (time.perf_counter() - start) * 1000.0

            is_allowed_prefix = waf.is_allowed_path(path)
            if not is_allowed_prefix:
                await waf.track_url(path, response.status_code)

            state_user = request.state.user_id
            state_job = request.state.job_id
            state_svc = request.state.service
            set_telemetry(
                status_code=response.status_code,
                user_id=state_user,
                job_id=state_job,
                service=state_svc,
            )
            _log_request(logger, client_ip, request.method, path, response.status_code, latency_ms)

            waf.record_traffic(
                request.method, path, client_ip, request.headers.get("user-agent", ""),
                "allow", "ok", 0.0, "unknown", response.status_code, latency_ms
            )
            _apply_security_headers(response, request_id, latency_ms, settings)
            if "guest_id" not in request.cookies:
                response.set_cookie("guest_id", guest_id, max_age=2592000, httponly=True, samesite="lax")
            if settings.is_development and path.startswith("/static/"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

            return response
        finally:
            request_id_ctx.reset(token)
            reset_telemetry(ctx_token)
