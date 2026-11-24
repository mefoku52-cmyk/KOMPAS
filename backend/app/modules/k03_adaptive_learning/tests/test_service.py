import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import insert

from app.core.database.session import Base
from app.modules.k03_adaptive_learning.services.service import K03Service
from app.shared.curriculum import Subject, Topic
from app.shared.identity import User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role, system_principal


def _sys(school_id):
    p = system_principal()
    return Principal(user_id=p.user_id, role=None, school_id=school_id, scopes=p.scopes, is_system=True)


def _setup(db_session):
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    t1 = uuid.uuid4()
    t2 = uuid.uuid4()
    t3 = uuid.uuid4()
    student_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    class_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27"))
    db_session.add(Subject(id=subject_id, school_id=school_id, name="Math"))
    db_session.add(Topic(id=t1, school_id=school_id, subject_id=subject_id, name="A", grade=5, order_index=1))
    db_session.add(Topic(id=t2, school_id=school_id, subject_id=subject_id, name="B", grade=5, order_index=2))
    db_session.add(Topic(id=t3, school_id=school_id, subject_id=subject_id, name="C", grade=5, order_index=3))
    db_session.add(User(id=student_id, school_id=school_id, username=f"st-{student_id}", full_name="S", password_hash="x"))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="5A", grade=5))
    db_session.add(Enrollment(school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=student_id))
    db_session.flush()
    db_session.execute(insert(Base.metadata.tables["school_class_teacher"]).values(id=uuid.uuid4(), school_id=school_id, class_group_id=class_id, teacher_user_id=teacher_id))
    db_session.commit()
    return dict(school_id=school_id, student_id=student_id, teacher_id=teacher_id, class_id=class_id, t1=t1, t2=t2, t3=t3)


def _insert_topic_state(db_session, *, school_id, student_id, topic_id, kind, status, evidence_attempt_ref, is_verification_evidence, ts):
    table = Base.metadata.tables["progress_topic_state"]
    db_session.execute(
        insert(table).values(
            id=uuid.uuid4(),
            school_id=school_id,
            student_user_id=student_id,
            topic_id=topic_id,
            kind=kind,
            status=status,
            evidence_attempt_ref=evidence_attempt_ref,
            is_verification_evidence=is_verification_evidence,
            valid_from=ts,
            valid_to=None,
            version=1,
            is_demo=False,
        )
    )


def test_k03_deterministic_explainable_recommendations(db_session):
    ctx = _setup(db_session)
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _insert_topic_state(db_session, school_id=ctx["school_id"], student_id=ctx["student_id"], topic_id=ctx["t1"], kind="practiced", status="in_progress_practice", evidence_attempt_ref="a1", is_verification_evidence=False, ts=ts)
    _insert_topic_state(db_session, school_id=ctx["school_id"], student_id=ctx["student_id"], topic_id=ctx["t2"], kind="covered", status="partially_mastered", evidence_attempt_ref="c1", is_verification_evidence=False, ts=ts)
    _insert_topic_state(db_session, school_id=ctx["school_id"], student_id=ctx["student_id"], topic_id=ctx["t3"], kind="verified", status="verified_mastery", evidence_attempt_ref="v1", is_verification_evidence=True, ts=ts)
    db_session.commit()

    svc = K03Service(db_session)
    student = Principal(user_id=ctx["student_id"], role=Role.STUDENT, school_id=ctx["school_id"])
    recs = svc.recommend_for_student(student, school_id=ctx["school_id"], student_user_id=ctx["student_id"])
    assert len(recs) == 2
    topics = {r["topic_id"] for r in recs}
    assert str(ctx["t3"]) not in topics
    assert all("Deterministic" in r["reason"] and r["reason"] for r in recs)
    assert all(r["suggested_action"] == "practice" for r in recs)


def test_k03_permissions(db_session):
    ctx = _setup(db_session)
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _insert_topic_state(db_session, school_id=ctx["school_id"], student_id=ctx["student_id"], topic_id=ctx["t1"], kind="practiced", status="in_progress_practice", evidence_attempt_ref="a1", is_verification_evidence=False, ts=ts)
    db_session.commit()
    svc = K03Service(db_session)
    teacher = Principal(user_id=ctx["teacher_id"], role=Role.TEACHER, school_id=ctx["school_id"])
    ok = svc.recommend_for_student(teacher, school_id=ctx["school_id"], student_user_id=ctx["student_id"], class_group_id=ctx["class_id"], teaches=True)
    assert isinstance(ok, list)
    assert isinstance(svc.recommend_for_student(teacher, school_id=ctx["school_id"], student_user_id=ctx["student_id"], class_group_id=ctx["class_id"], teaches=False), list)
    unassigned_teacher = Principal(user_id=uuid.uuid4(), role=Role.TEACHER, school_id=ctx["school_id"])
    with pytest.raises(PermissionError):
        svc.recommend_for_student(unassigned_teacher, school_id=ctx["school_id"], student_user_id=ctx["student_id"], class_group_id=ctx["class_id"], teaches=True)
    stranger = Principal(user_id=uuid.uuid4(), role=Role.STUDENT, school_id=ctx["school_id"])
    with pytest.raises(PermissionError):
        svc.recommend_for_student(stranger, school_id=ctx["school_id"], student_user_id=ctx["student_id"])
