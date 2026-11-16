import uuid

import pytest

from app.modules.k10_organization_center.services.service import K10Service
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role, system_principal


def _setup(db_session):
    school_id = uuid.uuid4()
    leader_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    other_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(User(id=leader_id, school_id=school_id, username=f"l-{leader_id}", full_name="L", password_hash="x"))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(User(id=other_id, school_id=school_id, username=f"o-{other_id}", full_name="O", password_hash="x"))
    db_session.commit()
    return school_id, leader_id, teacher_id, other_id


def test_k10_leadership_can_create_and_list_tasks(db_session):
    school_id, leader_id, _, _ = _setup(db_session)
    svc = K10Service(db_session)
    leader = Principal(user_id=leader_id, role=Role.LEADERSHIP, school_id=school_id)
    task = svc.create_task(leader, school_id=school_id, title="Plan")
    svc.create_plan(leader, school_id=school_id, name="Rocny plan")
    svc.assign_task(leader, school_id=school_id, task_id=task.id, assignee_user_id=leader_id)
    db_session.commit()
    rows = svc.list_tasks(leader, school_id)
    assert len(rows) == 1


def test_k10_teacher_same_school_allowed_student_denied(db_session):
    school_id, _, teacher_id, other_id = _setup(db_session)
    svc = K10Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    svc.create_task(teacher, school_id=school_id, title="Uloha")
    db_session.commit()
    assert len(svc.list_tasks(teacher, school_id)) == 1
    student = Principal(user_id=other_id, role=Role.STUDENT, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.list_tasks(student, school_id)
