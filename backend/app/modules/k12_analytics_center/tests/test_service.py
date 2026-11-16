import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import insert

from app.core.database.session import Base
from app.modules.k12_analytics_center.services.service import K12Service
from app.shared.curriculum import Subject, Topic
from app.shared.identity import User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role


def _setup_school(db_session, *, student_count: int):
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    class_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    leader_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27"))
    db_session.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="1A", grade=1))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(User(id=leader_id, school_id=school_id, username=f"l-{leader_id}", full_name="L", password_hash="x"))
    students = []
    for i in range(student_count):
        sid = uuid.uuid4()
        db_session.add(User(id=sid, school_id=school_id, username=f"s-{sid}", full_name=f"S{i}", password_hash="x"))
        db_session.add(Enrollment(id=uuid.uuid4(), school_id=school_id, school_year_id=year_id, student_user_id=sid, class_group_id=class_id))
        students.append(sid)
    db_session.commit()
    return school_id, class_id, teacher_id, leader_id, students


def _seed_states(db_session, school_id, student_ids):
    subject_id = uuid.uuid4()
    db_session.add(Subject(id=subject_id, school_id=school_id, name=f"Subj-{subject_id}"))
    db_session.commit()
    table = Base.metadata.tables["progress_topic_state"]
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for sid in student_ids:
        topic_id = uuid.uuid4()
        db_session.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name=f"T-{topic_id}", grade=1, order_index=1))
        db_session.commit()
        db_session.execute(insert(table).values(
            id=uuid.uuid4(),
            school_id=school_id,
            student_user_id=sid,
            topic_id=topic_id,
            kind="practiced",
            status="partially_mastered",
            evidence_attempt_ref=str(uuid.uuid4()),
            is_verification_evidence=False,
            valid_from=ts,
            valid_to=None,
            version=1,
            is_demo=False,
        ))
    db_session.commit()


def test_k12_suppresses_small_groups(db_session):
    school_id, _, teacher_id, _, students = _setup_school(db_session, student_count=4)
    _seed_states(db_session, school_id, students)
    svc = K12Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    out = svc.get_school_overview(teacher, school_id=school_id)
    assert out["suppressed"] is True
    assert out["total_students"] == 0


def test_k12_aggregates_and_individual_requires_purpose_and_audits(db_session):
    school_id, _, teacher_id, leader_id, students = _setup_school(db_session, student_count=5)
    _seed_states(db_session, school_id, students)
    svc = K12Service(db_session)
    leader = Principal(user_id=leader_id, role=Role.LEADERSHIP, school_id=school_id)
    out = svc.get_school_overview(leader, school_id=school_id)
    assert out["suppressed"] is False
    assert out["total_students"] == 5
    # individual without purpose denied
    with pytest.raises(PermissionError):
        svc.get_individual_progress(leader, school_id=school_id, student_user_id=students[0], purpose=None)
    # with purpose ok
    ind = svc.get_individual_progress(leader, school_id=school_id, student_user_id=students[0], purpose="support")
    assert ind["student_user_id"] == str(students[0])
    assert len(ind["items"]) == 1
    # purpose and actions audited
    from app.core.audit.logger import AuditLog
    purposes = [r.purpose for r in db_session.query(AuditLog).filter(AuditLog.action == "k12.get_individual_progress").all()]
    assert "support" in purposes
