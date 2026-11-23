from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.security.auth import hash_password
from app.modules.k19_sis_integration.domain.models import SISIdentityMap, SISSource
from app.modules.k19_sis_integration.services.sync_service import SISService
from app.shared.identity import GuardianLink, RoleAssignment, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role


def _mk_school(db_session):
    school = School(name=f"SIS Flow {uuid.uuid4()}")
    db_session.add(school); db_session.flush()
    year = SchoolYear(school_id=school.id, name="2026/27")
    db_session.add(year); db_session.flush()
    return school, year


def _mk_leader(db_session, school_id):
    user = User(school_id=school_id, username=f"leader-{uuid.uuid4().hex[:6]}", full_name="Leader", password_hash=hash_password("Password123!"), is_active=True)
    db_session.add(user); db_session.flush()
    db_session.add(RoleAssignment(user_id=user.id, school_id=school_id, role=Role.LEADERSHIP.value)); db_session.flush()
    return user


def _principal(user):
    return Principal(user_id=user.id, role=Role.LEADERSHIP, school_id=user.school_id)


class FakeProvider:
    provider_type = "edupage"
    def __init__(self, snapshot):
        self._snapshot = snapshot
    def healthcheck(self):
        return {"ok": True, "provider": "edupage"}
    def fetch_roster(self):
        return self._snapshot


def test_full_flow_new_student_transfer_parent_and_absence(db_session, monkeypatch):
    from app.integrations.sis.base import ExternalClass, ExternalClassTeacher, ExternalEnrollment, ExternalGuardianLink, ExternalPerson, RosterSnapshot

    school, year = _mk_school(db_session)
    leader = _mk_leader(db_session, school.id)
    svc = SISService(db_session)
    src = svc.create_source(_principal(leader), school_id=school.id, provider_type="edupage", name="EduPage", subdomain="demo", api_key="secret", is_enabled=True)
    db_session.commit()

    snap1 = RosterSnapshot(
        classes=[ExternalClass(external_id="C1", name="5A", grade=5), ExternalClass(external_id="C2", name="5B", grade=5)],
        teachers=[ExternalPerson(external_id="T1", full_name="Ucitel A")],
        students=[ExternalPerson(external_id="S1", full_name="Ziak A")],
        guardians=[ExternalPerson(external_id="P1", full_name="Rodic A")],
        enrollments=[ExternalEnrollment(student_external_id="S1", class_external_id="C1")],
        class_teachers=[ExternalClassTeacher(teacher_external_id="T1", class_external_id="C1")],
        guardian_links=[ExternalGuardianLink(guardian_external_id="P1", child_student_external_id="S1")],
    )
    monkeypatch.setattr(svc, "_provider_for_source", lambda source: FakeProvider(snap1))
    job1 = svc.run_sync(_principal(leader), school_id=school.id, source_id=src.id, mode="full")
    db_session.commit()
    assert job1["status"] in {"success", "partial"}
    assert len(db_session.execute(select(Enrollment).where(Enrollment.school_id == school.id)).scalars().all()) == 1

    # new student + transfer S1 to C2 + parent link remains
    snap2 = RosterSnapshot(
        classes=[ExternalClass(external_id="C1", name="5A", grade=5), ExternalClass(external_id="C2", name="5B", grade=5)],
        teachers=[ExternalPerson(external_id="T1", full_name="Ucitel A")],
        students=[ExternalPerson(external_id="S1", full_name="Ziak A"), ExternalPerson(external_id="S2", full_name="Ziak Novy")],
        guardians=[ExternalPerson(external_id="P1", full_name="Rodic A")],
        enrollments=[ExternalEnrollment(student_external_id="S1", class_external_id="C2"), ExternalEnrollment(student_external_id="S2", class_external_id="C1")],
        class_teachers=[ExternalClassTeacher(teacher_external_id="T1", class_external_id="C1")],
        guardian_links=[ExternalGuardianLink(guardian_external_id="P1", child_student_external_id="S1")],
    )
    monkeypatch.setattr(svc, "_provider_for_source", lambda source: FakeProvider(snap2))
    job2 = svc.run_sync(_principal(leader), school_id=school.id, source_id=src.id, mode="full")
    db_session.commit()
    assert job2["status"] in {"success", "partial"}
    s1 = db_session.execute(select(SISIdentityMap).where(SISIdentityMap.external_id == "S1", SISIdentityMap.entity_type == "student")).scalar_one()
    c2 = db_session.execute(select(ClassGroup).where(ClassGroup.school_id == school.id, ClassGroup.name == "5B")).scalar_one()
    enr_s1 = db_session.execute(select(Enrollment).where(Enrollment.student_user_id == s1.internal_id, Enrollment.school_year_id == year.id)).scalar_one()
    assert enr_s1.class_group_id == c2.id
    assert len(db_session.execute(select(GuardianLink).where(GuardianLink.school_id == school.id)).scalars().all()) == 1

    # absent student S2 - should become candidate, not deleted
    snap3 = RosterSnapshot(
        classes=[ExternalClass(external_id="C1", name="5A", grade=5), ExternalClass(external_id="C2", name="5B", grade=5)],
        teachers=[ExternalPerson(external_id="T1", full_name="Ucitel A")],
        students=[ExternalPerson(external_id="S1", full_name="Ziak A")],
        guardians=[ExternalPerson(external_id="P1", full_name="Rodic A")],
        enrollments=[ExternalEnrollment(student_external_id="S1", class_external_id="C2")],
        class_teachers=[ExternalClassTeacher(teacher_external_id="T1", class_external_id="C1")],
        guardian_links=[ExternalGuardianLink(guardian_external_id="P1", child_student_external_id="S1")],
    )
    monkeypatch.setattr(svc, "_provider_for_source", lambda source: FakeProvider(snap3))
    job3 = svc.run_sync(_principal(leader), school_id=school.id, source_id=src.id, mode="full")
    db_session.commit()
    assert any(c["external_id"] == "S2" for c in job3["summary"]["deactivated_candidates"])
    s2 = db_session.execute(select(SISIdentityMap).where(SISIdentityMap.external_id == "S2", SISIdentityMap.entity_type == "student")).scalar_one()
    assert db_session.get(User, s2.internal_id) is not None
