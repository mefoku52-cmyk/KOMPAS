from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    AppError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    TooManyRequestsError,
    install_error_handlers,
)


def _client() -> TestClient:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/app-error")
    def app_error():
        raise AppError(409, "conflict", "already_exists", {"field": "name"})

    @app.get("/permission")
    def permission():
        raise PermissionError("not_owner")

    @app.get("/value")
    def value():
        raise ValueError("invalid_transition")

    @app.get("/missing")
    def missing():
        raise LookupError("not_found")

    @app.get("/bad-request")
    def bad_request():
        raise BadRequestError("bad_input")

    @app.get("/forbidden")
    def forbidden():
        raise ForbiddenError()

    @app.get("/not-found")
    def not_found():
        raise NotFoundError()

    @app.get("/rate-limited")
    def rate_limited():
        raise TooManyRequestsError()

    return TestClient(app)


def test_app_error_format_and_request_id():
    client = _client()
    response = client.get("/app-error")
    assert response.status_code == 409
    body = response.json()["error"]
    assert body["code"] == "conflict"
    assert body["message_key"] == "already_exists"
    assert body["details"] == {"field": "name"}
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert len(body["request_id"]) == 36


def test_permission_value_lookup_mapping():
    client = _client()
    permission = client.get("/permission")
    assert permission.status_code == 403
    assert permission.json()["error"]["code"] == "forbidden"
    assert permission.json()["error"]["message_key"] == "not_owner"

    value = client.get("/value")
    assert value.status_code == 400
    assert value.json()["error"]["message_key"] == "invalid_transition"

    missing = client.get("/missing")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_helper_errors_and_validation_mapping():
    client = _client()
    assert client.get("/bad-request").status_code == 400
    assert client.get("/forbidden").json()["error"]["message_key"] == "forbidden"
    assert client.get("/not-found").json()["error"]["message_key"] == "not_found"
    limited = client.get("/rate-limited")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "rate_limited"


def test_request_id_is_preserved_from_error_response():
    client = _client()
    first = client.get("/value")
    second = client.get("/value")
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
