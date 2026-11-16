import uuid

import pytest

from app.modules.k11_operations_center.domain.models import OperationRequestStatus
from app.modules.k11_operations_center.services.service import K11Service
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role


def _setup(db_session):
    school_id = uuid.uuid4()
    leader_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    for uid, uname in [(leader_id, "l"), (teacher_id, "t"), (student_id, "s")]:
        db_session.add(User(id=uid, school_id=school_id, username=f"{uname}-{uid}", full_name=uname, password_hash="x"))
    db_session.commit()
    return school_id, leader_id, teacher_id, student_id


def test_k11_teacher_creates_and_leadership_transitions(db_session):
    school_id, leader_id, teacher_id, _ = _setup(db_session)
    svc = K11Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    leader = Principal(user_id=leader_id, role=Role.LEADERSHIP, school_id=school_id)
    req = svc.create_request(teacher, school_id=school_id, request_type="room", title="Ucebna")
    assert req.status == OperationRequestStatus.SUBMITTED.value
    req = svc.transition(leader, req.id, OperationRequestStatus.APPROVED.value)
    req = svc.transition(leader, req.id, OperationRequestStatus.IN_PROGRESS.value)
    req = svc.transition(leader, req.id, OperationRequestStatus.FULFILLED.value)
    db_session.commit()
    assert req.status == OperationRequestStatus.FULFILLED.value
    rows = svc.list_requests(leader, school_id)
    assert len(rows) == 1


def test_k11_invalid_transition_and_student_denied(db_session):
    school_id, leader_id, teacher_id, student_id = _setup(db_session)
    svc = K11Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    leader = Principal(user_id=leader_id, role=Role.LEADERSHIP, school_id=school_id)
    req = svc.create_request(teacher, school_id=school_id, request_type="equipment", title="Projektor")
    with pytest.raises(ValueError):
        svc.transition(leader, req.id, OperationRequestStatus.FULFILLED.value)
    student = Principal(user_id=student_id, role=Role.STUDENT, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.list_requests(student, school_id)
