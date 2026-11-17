from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config.settings import settings
from app.core.database.session import get_db
from app.core.ratelimit import InMemoryRateLimiter, reset_rate_limiter, set_rate_limiter


def test_in_memory_rate_limiter_window_and_reset():
    limiter = InMemoryRateLimiter()
    assert limiter.check("k", limit=2, window_seconds=60).allowed
    assert limiter.check("k", limit=2, window_seconds=60).allowed
    third = limiter.check("k", limit=2, window_seconds=60)
    assert third.allowed is False
    assert third.retry_after_seconds >= 1
    limiter.reset("k")
    assert limiter.check("k", limit=1, window_seconds=60).allowed


def test_login_rate_limit(db_session, monkeypatch):
    from app.main import create_app

    reset_rate_limiter()
    set_rate_limiter(InMemoryRateLimiter())
    monkeypatch.setattr(settings, "rate_limit_login_attempts", 2)
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    try:
        first = client.post("/auth/login", json={"username": "rate-limit", "password": "x"})
        second = client.post("/auth/login", json={"username": "rate-limit", "password": "x"})
        third = client.post("/auth/login", json={"username": "rate-limit", "password": "x"})
        assert first.status_code == 401
        assert second.status_code == 401
        assert third.status_code == 429
        assert third.json()["error"]["message_key"] == "rate_limited"
    finally:
        app.dependency_overrides.clear()
        reset_rate_limiter()
