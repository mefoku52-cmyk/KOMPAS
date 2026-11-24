from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security.auth import create_access_token, hash_password
from app.main import app
from app.modules.k19_sis_integration.domain.models import SISIdentityMap, SISSource, SISSyncJob
from app.modules.k19_sis_integration.services.sync_service import SISService
from app.shared.identity import GuardianLink, RoleAssignment, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role


def _mk_school(db_session):
    school = School(name=f"SIS School {uuid.uuid4()}")
    db_session.add(school)
    db_session.flush()
    year = SchoolYear(school_id=school.id, name="2026/27")
    db_session.add(year)
    db_session.flush()
    return school, year


def _mk_user(db_session, school_id, username, role: Role, full_name=None):
    user = User(school_id=school_id, username=username, full_name=full_name or username, password_hash=hash_password("Password123!"), is_active=True)
    db_session.add(user)
    db_session.flush()
    db_session.add(RoleAssignment(user_id=user.id, school_id=school_id, role=role.value))
    db_session.flush()
    return user


def _principal(user: User, role: Role) -> Principal:
    return Principal(user_id=user.id, role=role, school_id=user.school_id)


def _auth(user: User, role: Role):
    token = create_access_token(user.id, role, user.school_id)
    return {"Authorization": f"Bearer {token}"}


def test_sis_source_create_and_test_connection(db_session, monkeypatch):
    school, _ = _mk_school(db_session)
    leader = _mk_user(db_session, school.id, "leader1", Role.LEADERSHIP)
    svc = SISService(db_session)
    src = svc.create_source(_principal(leader, Role.LEADERSHIP), school_id=school.id, provider_type="edupage", name="EduPage", subdomain="demo-school", base_url="https://demo-school.edupage.org", api_key="secret-key", config={}, is_enabled=True)
    db_session.commit()

    class FakeProvider:
        provider_type = "edupage"
        def healthcheck(self):
            return {"ok": True, "provider": "edupage", "keys": ["teachers", "students", "classes"]}

    monkeypatch.setattr(svc, "_provider_for_source", lambda source: FakeProvider())
    result = svc.test_connection(_principal(leader, Role.LEADERSHIP), school_id=school.id, source_id=src.id)
    assert result["ok"] is True


def test_sis_sync_creates_updates_and_maps(db_session, monkeypatch):
    school, year = _mk_school(db_session)
    leader = _mk_user(db_session, school.id, "leader2", Role.LEADERSHIP)
    svc = SISService(db_session)
    src = svc.create_source(_principal(leader, Role.LEADERSHIP), school_id=school.id, provider_type="edupage", name="EduPage", subdomain="demo", api_key="secret-key", is_enabled=True)
    db_session.commit()

    class FakeProvider:
        provider_type = "edupage"
        def fetch_roster(self):
            from app.integrations.sis.base import RosterSnapshot, ExternalClass, ExternalPerson, ExternalEnrollment, ExternalClassTeacher, ExternalGuardianLink
            return RosterSnapshot(
                classes=[ExternalClass(external_id="C1", name="5A", grade=5), ExternalClass(external_id="C2", name="6A", grade=6)],
                teachers=[ExternalPerson(external_id="T1", full_name="Ucitel Jeden"), ExternalPerson(external_id="T2", full_name="Ucitel Dva")],
                students=[ExternalPerson(external_id="S1", full_name="Ziak Jeden"), ExternalPerson(external_id="S2", full_name="Ziak Dva")],
                guardians=[ExternalPerson(external_id="P1", full_name="Rodic Jeden")],
                enrollments=[ExternalEnrollment(student_external_id="S1", class_external_id="C1"), ExternalEnrollment(student_external_id="S2", class_external_id="C1")],
                class_teachers=[ExternalClassTeacher(teacher_external_id="T1", class_external_id="C1")],
                guardian_links=[ExternalGuardianLink(guardian_external_id="P1", child_student_external_id="S1", relationship="parent")],
            )

    monkeypatch.setattr(svc, "_provider_for_source", lambda source: FakeProvider())
    job = svc.run_sync(_principal(leader, Role.LEADERSHIP), school_id=school.id, source_id=src.id, mode="full")
    db_session.commit()

    assert job["status"] in {"success", "partial"}
    assert db_session.execute(select(User).where(User.school_id == school.id)).scalars().all()
    assert db_session.execute(select(ClassGroup).where(ClassGroup.school_id == school.id)).scalars().all()
    assert db_session.execute(select(Enrollment).where(Enrollment.school_id == school.id)).scalars().all()
    assert db_session.execute(select(GuardianLink).where(GuardianLink.school_id == school.id)).scalars().all()
    maps = db_session.execute(select(SISIdentityMap).where(SISIdentityMap.school_id == school.id)).scalars().all()
    assert any(m.entity_type == "student" and m.external_id == "S1" for m in maps)

    # update: move S2 to C2, rename teacher
    class FakeProvider2:
        provider_type = "edupage"
        def fetch_roster(self):
            from app.integrations.sis.base import RosterSnapshot, ExternalClass, ExternalPerson, ExternalEnrollment, ExternalClassTeacher, ExternalGuardianLink
            return RosterSnapshot(
                classes=[ExternalClass(external_id="C1", name="5A", grade=5), ExternalClass(external_id="C2", name="6A", grade=6)],
                teachers=[ExternalPerson(external_id="T1", full_name="Ucitel Jeden Upraveny"), ExternalPerson(external_id="T2", full_name="Ucitel Dva")],
                students=[ExternalPerson(external_id="S1", full_name="Ziak Jeden"), ExternalPerson(external_id="S2", full_name="Ziak Dva")],
                guardians=[ExternalPerson(external_id="P1", full_name="Rodic Jeden")],
                enrollments=[ExternalEnrollment(student_external_id="S1", class_external_id="C1"), ExternalEnrollment(student_external_id="S2", class_external_id="C2")],
                class_teachers=[ExternalClassTeacher(teacher_external_id="T1", class_external_id="C1")],
                guardian_links=[ExternalGuardianLink(guardian_external_id="P1", child_student_external_id="S1", relationship="parent")],
            )

    monkeypatch.setattr(svc, "_provider_for_source", lambda source: FakeProvider2())
    job2 = svc.run_sync(_principal(leader, Role.LEADERSHIP), school_id=school.id, source_id=src.id, mode="full")
    db_session.commit()
    assert job2["status"] in {"success", "partial"}

    t1_map = db_session.execute(select(SISIdentityMap).where(SISIdentityMap.external_id == "T1", SISIdentityMap.entity_type == "teacher")).scalar_one()
    t1 = db_session.get(User, t1_map.internal_id)
    assert t1.full_name == "Ucitel Jeden Upraveny"
    s2_map = db_session.execute(select(SISIdentityMap).where(SISIdentityMap.external_id == "S2", SISIdentityMap.entity_type == "student")).scalar_one()
    c2 = db_session.execute(select(ClassGroup).where(ClassGroup.name == "6A", ClassGroup.school_id == school.id)).scalar_one()
    enr = db_session.execute(select(Enrollment).where(Enrollment.student_user_id == s2_map.internal_id, Enrollment.school_year_id == year.id)).scalar_one()
    assert enr.class_group_id == c2.id


def test_sis_api_rbac(db_session):
    school, _ = _mk_school(db_session)
    leader = _mk_user(db_session, school.id, "leader3", Role.LEADERSHIP)
    teacher = _mk_user(db_session, school.id, "teacher3", Role.TEACHER)
    db_session.commit()

    from fastapi import FastAPI
    from app.core.database.session import get_db
    from app.core.security.auth import get_current_principal
    from app.modules.k19_sis_integration.api.router import router

    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_db] = lambda: db_session

    payload = {"provider_type": "edupage", "name": "EduPage", "subdomain": "demo", "api_key": "k", "is_enabled": False}

    test_app.dependency_overrides[get_current_principal] = lambda: _principal(teacher, Role.TEACHER)
    client = TestClient(test_app)
    r_forbidden = client.post("/integrations/sis/sources", json=payload)
    assert r_forbidden.status_code == 403

    test_app.dependency_overrides[get_current_principal] = lambda: _principal(leader, Role.LEADERSHIP)
    client = TestClient(test_app)
    r_ok = client.post("/integrations/sis/sources", json=payload)
    assert r_ok.status_code == 200
    body = r_ok.json()
    assert body["has_secret"] is True
    assert body["secret_masked"] != "k"

    r_list = client.get("/integrations/sis/sources")
    assert r_list.status_code == 200
    assert r_list.json()["total"] == 1


def test_edupage_rejects_non_edupage_or_non_https_base_url():
    import pytest
    from app.integrations.sis.edupage import EduPageProvider
    for url in ("http://school.edupage.org", "https://127.0.0.1", "https://attacker.example", "https://user:pass@school.edupage.org"):
        with pytest.raises(ValueError, match="invalid_edupage_base_url"):
            EduPageProvider(subdomain="school", api_key="secret", base_url=url)
