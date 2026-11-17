import uuid

from app.modules.k02_subject_workspace.repository.repository import K02Repository
from app.shared.curriculum import Subject
from app.shared.identity import User
from app.shared.school import School


def test_k02_repository_workspace_and_nodes(db_session):
    school_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    db_session.add(School(id=school_id, name="S"))
    db_session.flush()
    db_session.add(User(id=teacher_id, school_id=school_id, username="t", full_name="T", password_hash="x"))
    db_session.add(Subject(id=subject_id, school_id=school_id, name="Math"))
    db_session.flush()
    db_session.commit()

    repo = K02Repository(db_session)
    ws = repo.create_workspace(school_id=school_id, subject_id=subject_id, teacher_user_id=teacher_id, name="Plan")
    n1 = repo.add_node(school_id=school_id, workspace_id=ws.id, title="Root A", order_index=1)
    n2 = repo.add_node(school_id=school_id, workspace_id=ws.id, title="Child", parent_node_id=n1.id, order_index=0)
    db_session.commit()

    nodes = repo.list_nodes(ws.id)
    assert {n.title for n in nodes} == {"Root A", "Child"}
    assert repo.get_workspace(ws.id).teacher_user_id == teacher_id
