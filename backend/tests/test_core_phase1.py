import uuid
from datetime import timedelta

import pytest

from app.core.audit.logger import AuditLog, verify_chain, write as audit_write
from app.core.events.bus import DomainEvent, EventBus
from app.core.permissions.policy import Scope, Visibility, authorize
from app.core.security.auth import create_access_token, decode_access_token, hash_password, verify_password
from app.shared.identity import GuardianLink, RoleAssignment, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role, new_uuid, utc_now


def _principal(user_id=None, role=None, school_id=None):
    return Principal(user_id=user_id or uuid.uuid4(), role=role, school_id=school_id)


def test_authorize_deny_by_default():
    p = _principal(role=Role.STUDENT)
    d = authorize(p, "read", "res", context={}, db=None)
    assert d.allowed is False


def test_authorize_self_allowed_and_denied():
    uid = uuid.uuid4()
    p = _principal(user_id=uid, role=Role.STUDENT)
    ok = authorize(p, "read", "res", context={"scope": Scope.SELF, "owner_user_id": uid})
    bad = authorize(p, "read", "res", context={"scope": Scope.SELF, "owner_user_id": uuid.uuid4()})
    assert ok.allowed is True
    assert bad.allowed is False


def test_authorize_teacher_private_note():
    uid = uuid.uuid4()
    teacher = _principal(user_id=uid, role=Role.TEACHER)
    other = _principal(role=Role.STUDENT)
    ok = authorize(teacher, "read", "note", context={"visibility": Visibility.TEACHER_PRIVATE_NOTE, "owner_user_id": uid})
    bad = authorize(other, "read", "note", context={"visibility": Visibility.TEACHER_PRIVATE_NOTE, "owner_user_id": uid})
    assert ok.allowed is True
    assert bad.allowed is False


def test_authorize_parent_private_communication():
    uid = uuid.uuid4()
    other = uuid.uuid4()
    p = _principal(user_id=uid, role=Role.PARENT)
    ok = authorize(p, "read", "msg", context={"visibility": Visibility.PARENT_PRIVATE_COMMUNICATION, "participants": [uid, other]})
    bad = authorize(_principal(role=Role.TEACHER), "read", "msg", context={"visibility": Visibility.PARENT_PRIVATE_COMMUNICATION, "participants": [uid]})
    assert ok.allowed is True
    assert bad.allowed is False


def test_authorize_guardian_of(db_session):
    school_id = uuid.uuid4()
    guardian_id = uuid.uuid4()
    child_id = uuid.uuid4()
    db_session.add(School(id=school_id, name="S"))
    db_session.flush()
    db_session.add(User(id=guardian_id, school_id=school_id, username="g", full_name="G", password_hash="x"))
    db_session.add(User(id=child_id, school_id=school_id, username="c", full_name="C", password_hash="x"))
    db_session.flush()
    db_session.add(GuardianLink(guardian_user_id=guardian_id, child_user_id=child_id, school_id=school_id))
    db_session.commit()
    p = Principal(user_id=guardian_id, role=Role.PARENT, school_id=school_id)
    ok = authorize(p, "read", "child", context={"scope": Scope.GUARDIAN_OF, "student_user_id": child_id}, db=db_session)
    bad = authorize(p, "read", "child", context={"scope": Scope.GUARDIAN_OF, "student_user_id": uuid.uuid4()}, db=db_session)
    assert ok.allowed is True
    assert bad.allowed is False


def test_authorize_leadership_individual_requires_purpose():
    sid = uuid.uuid4()
    p = Principal(user_id=uuid.uuid4(), role=Role.LEADERSHIP, school_id=sid)
    ok = authorize(p, "read", "u", context={"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE, "school_id": sid, "purpose": "support"})
    bad = authorize(p, "read", "u", context={"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE, "school_id": sid, "purpose": ""})
    assert ok.allowed is True
    assert bad.allowed is False


def test_audit_chain_and_tamper_detection(db_session):
    p = _principal(role=Role.TEACHER)
    audit_write(db_session, p, "a1", "r1", None, "ok")
    audit_write(db_session, p, "a2", "r2", "p", "ok")
    db_session.commit()
    ok, bad_id = verify_chain(db_session)
    assert ok is True and bad_id is None
    tampered = AuditLog(
        id=new_uuid(),
        timestamp=utc_now(),
        principal_id=None,
        principal_role=None,
        school_id=None,
        action="tampered",
        resource="tampered",
        purpose=None,
        outcome="tampered",
        details="{}",
        prev_hash="0" * 64,
        record_hash="f" * 64,
    )
    db_session.add(tampered)
    db_session.commit()
    ok2, bad_id2 = verify_chain(db_session)
    assert ok2 is False
    assert bad_id2 is not None


def test_event_bus_handler_isolation_and_persist(db_session):
    bus = EventBus()
    called = {"ok": 0}

    def bad_handler(evt):
        raise RuntimeError("boom")

    def good_handler(evt):
        called["ok"] += 1

    bus.subscribe("t", bad_handler)
    bus.subscribe("t", good_handler)
    bus.publish(DomainEvent(event_type="t", school_id=None, payload={"x": 1}), db=db_session)
    db_session.commit()
    assert called["ok"] == 1
    from app.core.events.bus import EventLog
    assert db_session.query(EventLog).count() == 1


def test_auth_bad_password_and_expired_token(db_session):
    school_id = uuid.uuid4()
    uid = uuid.uuid4()
    pw_hash = hash_password("secret")
    db_session.add(School(id=school_id, name="S2"))
    db_session.flush()
    db_session.add(User(id=uid, school_id=school_id, username="u1", full_name="U1", password_hash=pw_hash))
    db_session.flush()
    db_session.add(RoleAssignment(user_id=uid, school_id=school_id, role=Role.STUDENT.value))
    db_session.commit()
    assert verify_password("secret", pw_hash) is True
    assert verify_password("wrong", pw_hash) is False
    tok = create_access_token(uid, Role.STUDENT, school_id, expires_delta=timedelta(seconds=-10))
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        decode_access_token(tok)


def test_audit_log_append_only(db_session):
    p = _principal(role=Role.TEACHER)
    audit_write(db_session, p, "a", "r", None, "ok")
    db_session.commit()
    row = db_session.query(AuditLog).first()
    row.outcome = "tampered"
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    row = db_session.query(AuditLog).first()
    db_session.delete(row)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()
