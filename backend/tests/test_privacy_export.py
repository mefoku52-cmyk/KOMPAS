from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.audit.logger import AuditLog
from app.core.database.session import get_db
from app.core.security.auth import create_access_token, hash_password
from app.shared.identity import GuardianLink, RoleAssignment, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Role


@pytest.fixture()
def privacy_api(db_session):
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    yield client, db_session
    app.dependency_overrides.clear()


def _user(db, school_id, role, name):
    user = User(
        id=uuid.uuid4(), school_id=school_id, username=f"{name}-{uuid.uuid4()}",
        full_name=name.title(), password_hash=hash_password("DemoPass1234"), is_demo=True,
    )
    db.add(user)
    db.flush()
    db.add(RoleAssignment(user_id=user.id, school_id=school_id, role=role.value, is_demo=True))
    return user


def _headers(user, role):
    return {"Authorization": f"Bearer {create_access_token(user.id, role, user.school_id)}"}


def test_student_export_roles_and_audit(privacy_api):
    client, db = privacy_api
    school = School(name=f"Privacy-{uuid.uuid4()}", is_demo=True)
    other_school = School(name=f"Other-{uuid.uuid4()}", is_demo=True)
    db.add_all([school, other_school])
    db.flush()
    year = SchoolYear(school_id=school.id, name="2026/2027", is_demo=True)
    db.add(year)
    db.flush()
    class_group = ClassGroup(school_id=school.id, school_year_id=year.id, name="7.A", grade=7, is_demo=True)
    db.add(class_group)
    db.flush()
    student = _user(db, school.id, Role.STUDENT, "student")
    parent = _user(db, school.id, Role.PARENT, "parent")
    stranger = _user(db, school.id, Role.PARENT, "stranger")
    teacher = _user(db, school.id, Role.TEACHER, "teacher")
    leadership = _user(db, school.id, Role.LEADERSHIP, "leader")
    foreign_leader = _user(db, other_school.id, Role.LEADERSHIP, "foreign")
    db.flush()
    db.add(GuardianLink(guardian_user_id=parent.id, child_user_id=student.id, school_id=school.id, is_demo=True))
    db.add(Enrollment(
        school_id=school.id, school_year_id=year.id, class_group_id=class_group.id,
        student_user_id=student.id, is_demo=True,
    ))
    db.commit()
    url = f"/privacy/students/{student.id}/export?purpose=parent_request"

    assert client.get(url).status_code == 401
    assert client.get(url, headers=_headers(stranger, Role.PARENT)).status_code == 403
    assert client.get(url, headers=_headers(teacher, Role.TEACHER)).status_code == 403
    assert client.get(url, headers=_headers(foreign_leader, Role.LEADERSHIP)).status_code == 403
    assert client.get(
        f"/privacy/students/{student.id}/export", headers=_headers(student, Role.STUDENT),
    ).status_code == 422

    for user, role in ((student, Role.STUDENT), (parent, Role.PARENT), (leadership, Role.LEADERSHIP)):
        response = client.get(url, headers=_headers(user, role))
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["purpose"] == "parent_request"
        assert payload["identity"]["id"] == str(student.id)
        assert "password_hash" not in payload["identity"]
        assert len(payload["enrollments"]) == 1
        assert payload["enrollments"][0]["class_group"]["name"] == "7.A"

    entries = db.execute(select(AuditLog).where(AuditLog.action == "privacy.export_student_data")).scalars().all()
    assert len(entries) == 3
    assert all(entry.purpose == "parent_request" for entry in entries)
    assert all(entry.outcome == "success" for entry in entries)
