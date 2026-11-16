import uuid

import pytest

from app.modules.k02_subject_workspace.services.service import K02Service
from app.shared.curriculum import Subject
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role, system_principal


def _setup(db_session):
    school_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    other_teacher = uuid.uuid4()
    leader_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(User(id=other_teacher, school_id=school_id, username=f"o-{other_teacher}", full_name="O", password_hash="x"))
    db_session.add(User(id=leader_id, school_id=school_id, username=f"l-{leader_id}", full_name="L", password_hash="x"))
    db_session.add(Subject(id=subject_id, school_id=school_id, name="Math"))
    db_session.commit()
    return school_id, teacher_id, other_teacher, leader_id, subject_id


def test_k02_teacher_can_manage_own_workspace_and_tree(db_session):
    school_id, teacher_id, _, _, subject_id = _setup(db_session)
    svc = K02Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    ws = svc.create_workspace(teacher, school_id=school_id, subject_id=subject_id, teacher_user_id=teacher_id, name="Plan")
    n1 = svc.add_node(teacher, ws.id, title="Tema 1", order_index=1)
    n2 = svc.add_node(teacher, ws.id, title="Podtema", parent_node_id=n1.id, order_index=0)
    db_session.commit()
    got = svc.get_workspace(teacher, ws.id)
    assert got.id == ws.id
    nodes = svc.list_nodes(teacher, ws.id)
    assert [n.title for n in nodes] == ["Tema 1", "Podtema"] or {n.title for n in nodes} == {"Tema 1", "Podtema"}


def test_k02_other_teacher_denied(db_session):
    school_id, teacher_id, other_id, _, subject_id = _setup(db_session)
    svc = K02Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    ws = svc.create_workspace(teacher, school_id=school_id, subject_id=subject_id, teacher_user_id=teacher_id, name="Plan")
    db_session.commit()
    other = Principal(user_id=other_id, role=Role.TEACHER, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.add_node(other, ws.id, title="X")
    with pytest.raises(PermissionError):
        svc.list_nodes(other, ws.id)


def test_k02_leadership_requires_purpose_for_view(db_session):
    school_id, teacher_id, _, leader_id, subject_id = _setup(db_session)
    svc = K02Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    ws = svc.create_workspace(teacher, school_id=school_id, subject_id=subject_id, teacher_user_id=teacher_id, name="Plan")
    db_session.commit()
    leader = Principal(user_id=leader_id, role=Role.LEADERSHIP, school_id=school_id)
    rows = svc.list_nodes(leader, ws.id, purpose="oversight")
    assert rows == []
    with pytest.raises(PermissionError):
        svc.list_nodes(leader, ws.id, purpose="")
