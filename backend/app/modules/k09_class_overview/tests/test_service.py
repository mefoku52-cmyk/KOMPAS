import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import insert

from app.core.database.session import Base
from app.modules.k09_class_overview.services.service import K09Service
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
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    other_teacher = uuid.uuid4()
    student_id = uuid.uuid4()

    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27"))
    db_session.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="5A", grade=5))
    db_session.add(Subject(id=subject_id, school_id=school_id, name="Math"))
    db_session.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name="T", grade=5, order_index=1))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(User(id=other_teacher, school_id=school_id, username=f"o-{other_teacher}", full_name="O", password_hash="x"))
    db_session.add(User(id=student_id, school_id=school_id, username=f"s-{student_id}", full_name="S", password_hash="x"))
    db_session.add(Enrollment(school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=student_id))

    ct = Base.metadata.tables["school_class_teacher"]
    db_session.flush()
    db_session.execute(insert(ct).values(id=uuid.uuid4(), school_id=school_id, class_group_id=class_id, teacher_user_id=teacher_id, valid_from=datetime.now(timezone.utc), valid_to=None, version=1, is_demo=False))

    db_session.commit()

    table = Base.metadata.tables["progress_topic_state"]
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    db_session.flush()
    db_session.execute(insert(table).values(id=uuid.uuid4(), school_id=school_id, student_user_id=student_id, topic_id=topic_id, kind="practiced", status="in_progress_practice", evidence_attempt_ref="a1", is_verification_evidence=False, valid_from=ts, valid_to=None, version=1, is_demo=False))
    db_session.commit()
    return dict(school_id=school_id, class_id=class_id, teacher_id=teacher_id, other_teacher=other_teacher, student_id=student_id, topic_id=topic_id)


def test_k09_teacher_can_view_own_class_overview(db_session):
    ctx = _setup(db_session)
    svc = K09Service(db_session)
    teacher = Principal(user_id=ctx["teacher_id"], role=Role.TEACHER, school_id=ctx["school_id"])
    out = svc.get_class_overview(teacher, school_id=ctx["school_id"], class_group_id=ctx["class_id"])
    assert out["total_students"] == 1
    assert out["by_status"].get("in_progress_practice") == 1


def test_k09_non_teaching_teacher_denied(db_session):
    ctx = _setup(db_session)
    svc = K09Service(db_session)
    other = Principal(user_id=ctx["other_teacher"], role=Role.TEACHER, school_id=ctx["school_id"])
    with pytest.raises(PermissionError):
        svc.get_class_overview(other, school_id=ctx["school_id"], class_group_id=ctx["class_id"])


def test_k09_system_can_view(db_session):
    ctx = _setup(db_session)
    svc = K09Service(db_session)
    sp = _sys(ctx["school_id"])
    out = svc.get_class_overview(sp, school_id=ctx["school_id"], class_group_id=ctx["class_id"])
    assert out["tracked_student_topic_pairs"] == 1
