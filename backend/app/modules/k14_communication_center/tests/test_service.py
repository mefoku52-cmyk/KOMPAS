import uuid

import pytest

from app.modules.k14_communication_center.services.service import K14Service
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role


def _setup(db_session):
    school_id = uuid.uuid4()
    u1 = uuid.uuid4()
    u2 = uuid.uuid4()
    u3 = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    for uid, name in [(u1, "a"), (u2, "b"), (u3, "c")]:
        db_session.add(User(id=uid, school_id=school_id, username=f"{name}-{uid}", full_name=name, password_hash="x"))
    db_session.commit()
    return school_id, u1, u2, u3


def test_k14_participants_can_communicate_and_access_audited(db_session):
    school_id, u1, u2, _ = _setup(db_session)
    svc = K14Service(db_session)
    p1 = Principal(user_id=u1, role=Role.TEACHER, school_id=school_id)
    p2 = Principal(user_id=u2, role=Role.PARENT, school_id=school_id)
    thread = svc.create_thread(p1, school_id=school_id, subject="Info", participant_user_ids=[u2], is_private=True)
    svc.post_message(p1, thread_id=thread.id, body="Ahoj")
    db_session.commit()
    msgs = svc.list_messages(p2, thread_id=thread.id)
    assert len(msgs) == 1 and msgs[0].body == "Ahoj"
    # content access audited
    from app.core.audit.logger import AuditLog
    actions = [r.action for r in db_session.query(AuditLog).filter(AuditLog.resource == f"communication_thread:{thread.id}").all()]
    assert "k14.read_messages" in actions


def test_k14_private_thread_hidden_from_non_participants(db_session):
    school_id, u1, u2, u3 = _setup(db_session)
    svc = K14Service(db_session)
    p1 = Principal(user_id=u1, role=Role.TEACHER, school_id=school_id)
    p3 = Principal(user_id=u3, role=Role.TEACHER, school_id=school_id)
    thread = svc.create_thread(p1, school_id=school_id, subject="Sukromne", participant_user_ids=[u2], is_private=True)
    db_session.commit()
    with pytest.raises(PermissionError):
        svc.list_messages(p3, thread_id=thread.id)
    with pytest.raises(PermissionError):
        svc.post_message(p3, thread_id=thread.id, body="x")
    threads_u3 = svc.list_threads(p3, school_id=school_id)
    assert all(t.id != thread.id for t in threads_u3)
