import uuid

import pytest

from app.modules.k01_learning_profile.services.service import K01Service
from app.shared.identity import GuardianLink, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role, system_principal


def _setup_base(db_session):
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    student_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    leader_id = uuid.uuid4()
    other_id = uuid.uuid4()
    class_id = uuid.uuid4()

    db_session.add(School(id=school_id, name=f"School-{school_id}"))
    db_session.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27"))
    for uid, uname in [(student_id, "stud"), (parent_id, "parent"), (teacher_id, "teach"), (leader_id, "lead"), (other_id, "other")]:
        db_session.add(User(id=uid, school_id=school_id, username=f"{uname}-{uid}", full_name=uname, password_hash="x"))
    db_session.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="5A", grade=5))
    db_session.add(Enrollment(school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=student_id))
    db_session.add(GuardianLink(guardian_user_id=parent_id, child_user_id=student_id, school_id=school_id))
    db_session.commit()
    return {
        "school_id": school_id,
        "year_id": year_id,
        "student_id": student_id,
        "parent_id": parent_id,
        "teacher_id": teacher_id,
        "leader_id": leader_id,
        "other_id": other_id,
        "class_id": class_id,
    }


def test_k01_create_and_history_as_system(db_session):
    ctx = _setup_base(db_session)
    svc = K01Service(db_session)
    sp = system_principal()
    sp = Principal(user_id=sp.user_id, role=None, school_id=ctx["school_id"], scopes=sp.scopes, is_system=True)
    p1 = svc.create_profile(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], school_year_id=ctx["year_id"], grade=5, version=1)
    p2 = svc.create_profile(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], school_year_id=ctx["year_id"], grade=5, version=2, label="rev")
    db_session.commit()
    hist = svc.list_history(sp, ctx["student_id"], ctx["school_id"])
    assert [p.version for p in hist] == [1, 2]
    assert hist[0].id != hist[1].id
    latest = svc.get_latest_for_year(sp, ctx["student_id"], ctx["year_id"], ctx["school_id"])
    assert latest and latest.version == 2


def test_k01_student_can_view_self_history(db_session):
    ctx = _setup_base(db_session)
    svc = K01Service(db_session)
    sp = Principal(user_id=system_principal().user_id, role=None, school_id=ctx["school_id"], scopes=("system",), is_system=True)
    svc.create_profile(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], school_year_id=ctx["year_id"], grade=5, version=1)
    db_session.commit()
    student = Principal(user_id=ctx["student_id"], role=Role.STUDENT, school_id=ctx["school_id"])
    rows = svc.list_history(student, ctx["student_id"], ctx["school_id"])
    assert len(rows) == 1


def test_k01_parent_guardian_can_view_and_other_denied(db_session):
    ctx = _setup_base(db_session)
    svc = K01Service(db_session)
    sp = Principal(user_id=system_principal().user_id, role=None, school_id=ctx["school_id"], scopes=("system",), is_system=True)
    svc.create_profile(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], school_year_id=ctx["year_id"], grade=5, version=1)
    db_session.commit()
    parent = Principal(user_id=ctx["parent_id"], role=Role.PARENT, school_id=ctx["school_id"])
    rows = svc.list_history(parent, ctx["student_id"], ctx["school_id"])
    assert len(rows) == 1
    other_parent = Principal(user_id=ctx["other_id"], role=Role.PARENT, school_id=ctx["school_id"])
    with pytest.raises(PermissionError):
        svc.list_history(other_parent, ctx["student_id"], ctx["school_id"])


def test_k01_teacher_requires_teaches_class_and_leadership_requires_purpose(db_session):
    ctx = _setup_base(db_session)
    svc = K01Service(db_session)
    sp = Principal(user_id=system_principal().user_id, role=None, school_id=ctx["school_id"], scopes=("system",), is_system=True)
    svc.create_profile(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], school_year_id=ctx["year_id"], grade=5, version=1)
    db_session.commit()
    teacher = Principal(user_id=ctx["teacher_id"], role=Role.TEACHER, school_id=ctx["school_id"])
    ok = svc.list_history(teacher, ctx["student_id"], ctx["school_id"], class_group_id=ctx["class_id"], teaches=True)
    assert len(ok) == 1
    with pytest.raises(PermissionError):
        svc.list_history(teacher, ctx["student_id"], ctx["school_id"], class_group_id=ctx["class_id"], teaches=False)

    leader = Principal(user_id=ctx["leader_id"], role=Role.LEADERSHIP, school_id=ctx["school_id"])
    ok2 = svc.list_history(leader, ctx["student_id"], ctx["school_id"], purpose="support_review")
    assert len(ok2) == 1
    with pytest.raises(PermissionError):
        svc.list_history(leader, ctx["student_id"], ctx["school_id"], purpose="")
