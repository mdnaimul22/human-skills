from __future__ import annotations

import uuid

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import Settings, setup_logger
from src.config.logger import request_id_ctx
from src.helpers.exceptions import AppError, ErrorClassification, sanitize_client_error
from src.helpers.sanitizers import sanitize_client_path

logger = setup_logger(Settings.LOG_DIR / "router.log", name="helpers.error_handlers")

def _get_trace_id(request: Request) -> str:
    trace_id = request_id_ctx.get(None)
    if trace_id:
        return trace_id
    try:
        state_id = request.state.request_id
        if state_id:
            return str(state_id)
    except AttributeError as err:
        logger.debug(f"Request state has no request_id: {err}")
    header_id = request.headers.get("X-Request-ID")
    if header_id:
        return header_id
    return uuid.uuid4().hex[:8]

def register_error_handlers(app, app_logger=None) -> None:
    handler_logger = app_logger or logger

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(PydanticValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError | PydanticValidationError,
    ) -> JSONResponse:
        trace_id = _get_trace_id(request)
        errors = sanitize_client_path(jsonable_encoder(exc.errors(), custom_encoder={Exception: str}))
        handler_logger.error(
            f"Validation Error on {request.url.path}: {errors}",
            extra={
                "trace_id": trace_id,
                "error_code": "VALIDATION_ERROR",
                "error_type": exc.__class__.__name__,
                "classification": ErrorClassification.CLIENT_ERROR.value,
                "endpoint": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "status_code": 422,
                "trace_id": trace_id,
                "detail": errors,
            },
            headers={"X-Request-ID": trace_id},
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        trace_id = _get_trace_id(request)
        user_msg = sanitize_client_path(sanitize_client_error(exc.message))
        error_code = exc.error_code
        classification_val = exc.classification.value
        detail = sanitize_client_path(exc.details.get("detail")) if exc.details else None
        handler_logger.error(
            f"{exc.__class__.__name__} [{error_code}] on {request.url.path}: {exc.message}",
            extra={
                "trace_id": trace_id,
                "error_code": error_code,
                "error_type": exc.__class__.__name__,
                "classification": classification_val,
                "details": exc.details,
                "endpoint": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": user_msg,
                "error_code": error_code,
                "status_code": exc.status_code,
                "trace_id": trace_id,
                "detail": detail,
            },
            headers={"X-Request-ID": trace_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        trace_id = _get_trace_id(request)
        error_code = f"HTTP_{exc.status_code}"
        if 400 <= exc.status_code < 500:
            if exc.status_code in (401, 403):
                classification_val = ErrorClassification.AUTH_ERROR.value
            elif exc.status_code == 429:
                classification_val = ErrorClassification.RATE_LIMIT.value
            else:
                classification_val = ErrorClassification.CLIENT_ERROR.value
        else:
            classification_val = ErrorClassification.SYSTEM_ERROR.value

        user_msg = sanitize_client_path(sanitize_client_error(str(exc.detail)))
        sanitized_detail = sanitize_client_path(exc.detail)
        handler_logger.error(
            f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}",
            extra={
                "trace_id": trace_id,
                "error_code": error_code,
                "error_type": exc.__class__.__name__,
                "classification": classification_val,
                "endpoint": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": user_msg,
                "error_code": error_code,
                "status_code": exc.status_code,
                "trace_id": trace_id,
                "detail": sanitized_detail,
            },
            headers={"X-Request-ID": trace_id},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_id = _get_trace_id(request)
        handler_logger.error(
            f"Unhandled Exception on {request.url.path}: {exc}",
            exc_info=True,
            extra={
                "trace_id": trace_id,
                "error_code": "INTERNAL_SERVER_ERROR",
                "error_type": exc.__class__.__name__,
                "classification": ErrorClassification.SYSTEM_ERROR.value,
                "endpoint": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "status_code": 500,
                "trace_id": trace_id,
                "detail": None,
            },
            headers={"X-Request-ID": trace_id},
        )
