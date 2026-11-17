from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

_REQUEST_ID_HEADER = "X-Request-ID"


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message_key: str,
        details: Any = None,
    ) -> None:
        super().__init__(message_key)
        self.status_code = status_code
        self.code = code
        self.message_key = message_key
        self.details = details


class BadRequestError(AppError):
    def __init__(self, message_key: str, details: Any = None) -> None:
        super().__init__(400, "bad_request", message_key, details)


class UnauthorizedError(AppError):
    def __init__(self, message_key: str = "unauthorized", details: Any = None) -> None:
        super().__init__(401, "unauthorized", message_key, details)


class ForbiddenError(AppError):
    def __init__(self, message_key: str = "forbidden", details: Any = None) -> None:
        super().__init__(403, "forbidden", message_key, details)


class NotFoundError(AppError):
    def __init__(self, message_key: str = "not_found", details: Any = None) -> None:
        super().__init__(404, "not_found", message_key, details)


class ConflictError(AppError):
    def __init__(self, message_key: str, details: Any = None) -> None:
        super().__init__(409, "conflict", message_key, details)


class TooManyRequestsError(AppError):
    def __init__(self, message_key: str = "rate_limited", details: Any = None) -> None:
        super().__init__(429, "rate_limited", message_key, details)


def get_request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if rid:
        return str(rid)
    return request.headers.get(_REQUEST_ID_HEADER) or str(uuid.uuid4())


def error_response(request: Request, status_code: int, code: str, message_key: str, details: Any = None) -> JSONResponse:
    request_id = get_request_id(request)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message_key": message_key,
                "request_id": request_id,
                "details": details,
            }
        },
        headers={_REQUEST_ID_HEADER: request_id},
    )


def _status_code_for_http(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        413: "payload_too_large",
        422: "validation_error",
        429: "rate_limited",
        500: "internal_error",
    }
    return mapping.get(status_code, "http_error")


def install_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers[_REQUEST_ID_HEADER] = request.state.request_id
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return error_response(request, exc.status_code, exc.code, exc.message_key, exc.details)

    @app.exception_handler(PermissionError)
    async def handle_permission_error(request: Request, exc: PermissionError):
        return error_response(request, 403, "forbidden", str(exc) or "forbidden")

    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError):
        return error_response(request, 400, "bad_request", str(exc) or "invalid_request")

    @app.exception_handler(LookupError)
    async def handle_lookup_error(request: Request, exc: LookupError):
        return error_response(request, 404, "not_found", str(exc) or "not_found")

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return error_response(request, 422, "validation_error", "validation_error", exc.errors())

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "message_key" in detail:
            return error_response(request, exc.status_code, str(detail.get("code") or _status_code_for_http(exc.status_code)), str(detail["message_key"]), detail.get("details"))
        return error_response(request, exc.status_code, _status_code_for_http(exc.status_code), str(detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.exception("unhandled error", extra={"request_id": get_request_id(request)})
        return error_response(request, 500, "internal_error", "internal_error")
