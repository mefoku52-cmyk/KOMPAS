from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config.settings import settings
from app.core.database.session import get_db
from app.core.ratelimit import InMemoryRateLimiter, reset_rate_limiter, set_rate_limiter
from app.core.security.auth import create_access_token, decode_access_token, hash_password
from app.shared.identity import RoleAssignment, User
from app.shared.school import School
from app.shared.types import Role


def _seed_user(db, *, role: Role = Role.STUDENT, password: str = "DemoPass1234", username: str | None = None) -> tuple[uuid.UUID, uuid.UUID]:
    school_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db.add(School(id=school_id, name=f"AuthSchool-{school_id}", is_demo=True))
    db.add(User(
        id=user_id, school_id=school_id, username=username or f"auth-{user_id}",
        full_name="Demo User", password_hash=hash_password(password), is_demo=True,
    ))
    db.add(RoleAssignment(id=uuid.uuid4(), user_id=user_id, school_id=school_id, role=role.value, is_demo=True))
    db.commit()
    return school_id, user_id


@pytest.fixture()
def auth_api(db_session):
    reset_rate_limiter()
    set_rate_limiter(InMemoryRateLimiter())
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    yield client, db_session
    app.dependency_overrides.clear()
    reset_rate_limiter()


def test_login_token_claims_and_logout_revocation(auth_api):
    client, db = auth_api
    school_id, user_id = _seed_user(db, username="auth-logout")
    response = client.post("/auth/login", json={"username": "auth-logout", "password": "DemoPass1234"})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    assert response.json()["expires_in"] == settings.jwt_access_token_expire_minutes * 60
    payload = decode_access_token(token)
    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_audience
    assert payload["jti"]
    assert payload["sub"] == str(user_id)

    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/k01/status", headers=headers).status_code == 200
    logout = client.post("/auth/logout", headers=headers)
    assert logout.status_code == 200, logout.text
    revoked = client.get("/k01/status", headers=headers)
    assert revoked.status_code == 401
    assert revoked.json()["error"]["message_key"] == "token_revoked"


def test_change_password_policy_and_invalidation(auth_api):
    client, db = auth_api
    _seed_user(db, username="auth-change")
    login = client.post("/auth/login", json={"username": "auth-change", "password": "DemoPass1234"})
    old_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {old_token}"}

    weak = client.post("/auth/change-password", headers=headers, json={
        "current_password": "DemoPass1234", "new_password": "short",
    })
    assert weak.status_code == 400
    assert weak.json()["error"]["message_key"] == "password_too_short"

    changed = client.post("/auth/change-password", headers=headers, json={
        "current_password": "DemoPass1234", "new_password": "NoveHeslo1234",
    })
    assert changed.status_code == 200, changed.text

    invalidated = client.get("/k01/status", headers=headers)
    assert invalidated.status_code == 401
    assert invalidated.json()["error"]["message_key"] == "token_expired_by_password_change"

    relogin = client.post("/auth/login", json={"username": "auth-change", "password": "NoveHeslo1234"})
    assert relogin.status_code == 200, relogin.text


def test_lockout_after_repeated_failures(auth_api):
    client, db = auth_api
    _seed_user(db, username="auth-lock")
    for attempt in range(settings.login_max_failures):
        response = client.post("/auth/login", json={"username": "auth-lock", "password": "wrong-password"})
        if attempt < settings.login_max_failures - 1:
            assert response.status_code == 401, response.text
        else:
            assert response.status_code == 429, response.text
            assert response.json()["error"]["message_key"] == "account_locked"

    reset_rate_limiter()
    locked = client.post("/auth/login", json={"username": "auth-lock", "password": "DemoPass1234"})
    assert locked.status_code == 429
    assert locked.json()["error"]["message_key"] == "account_locked"

    user = db.execute(select(User).where(User.username == "auth-lock")).scalars().one()
    assert user.locked_until is not None
    assert user.failed_login_count >= settings.login_max_failures
