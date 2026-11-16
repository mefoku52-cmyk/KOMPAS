import uuid

import pytest

from app.modules.k15_collaboration_projects.services.service import K15Service
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role


def _setup(db_session):
    school_id = uuid.uuid4()
    owner = uuid.uuid4()
    member = uuid.uuid4()
    outsider = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    for uid, n in [(owner, "o"), (member, "m"), (outsider, "x")]:
        db_session.add(User(id=uid, school_id=school_id, username=f"{n}-{uid}", full_name=n, password_hash="x"))
    db_session.commit()
    return school_id, owner, member, outsider


def test_k15_project_members_can_manage_tasks_and_submissions(db_session):
    school_id, owner, member, outsider = _setup(db_session)
    svc = K15Service(db_session)
    p_owner = Principal(user_id=owner, role=Role.TEACHER, school_id=school_id)
    p_member = Principal(user_id=member, role=Role.STUDENT, school_id=school_id)  # cross-grade member allowed
    project = svc.create_project(p_owner, school_id=school_id, title="Projekt", member_user_ids=[member])
    task = svc.create_task(p_member, project_id=project.id, title="Uloha")
    sub = svc.submit(p_member, task_id=task.id, content="odovzdanie")
    db_session.commit()
    tasks = svc.list_tasks(p_owner, project_id=project.id)
    assert len(tasks) == 1 and tasks[0].id == task.id
    subs = svc.list_submissions(p_owner, task_id=task.id)
    assert len(subs) == 1 and subs[0].id == sub.id


def test_k15_non_member_denied(db_session):
    school_id, owner, member, outsider = _setup(db_session)
    svc = K15Service(db_session)
    p_owner = Principal(user_id=owner, role=Role.TEACHER, school_id=school_id)
    p_out = Principal(user_id=outsider, role=Role.STUDENT, school_id=school_id)
    project = svc.create_project(p_owner, school_id=school_id, title="P", member_user_ids=[member])
    with pytest.raises(PermissionError):
        svc.list_tasks(p_out, project_id=project.id)
    task = svc.create_task(p_owner, project_id=project.id, title="T")
    with pytest.raises(PermissionError):
        svc.submit(p_out, task_id=task.id, content="x")
