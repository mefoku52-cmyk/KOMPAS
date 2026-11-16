import uuid

import pytest

from app.core.events.bus import DomainEvent, EventBus
from app.modules.k04_missions.domain.models import TaskType
from app.modules.k04_missions.repository.repository import K04Repository
from app.modules.k04_missions.services.service import K04Service, evaluate_answer
from app.shared.curriculum import Subject, Topic
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role, system_principal


def _sys(school_id):
    p = system_principal()
    return Principal(user_id=p.user_id, role=None, school_id=school_id, scopes=p.scopes, is_system=True)


def _setup(db_session):
    school_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    student_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(Subject(id=subject_id, school_id=school_id, name="Math"))
    db_session.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name="T", grade=5, order_index=1))
    db_session.add(User(id=student_id, school_id=school_id, username=f"st-{student_id}", full_name="S", password_hash="x"))
    db_session.commit()
    return school_id, topic_id, student_id


def test_k04_deterministic_evaluation():
    assert evaluate_answer(TaskType.CHOICE, "A", "a") is True
    assert evaluate_answer(TaskType.NUMERIC, "3.0", "3") is True
    assert evaluate_answer(TaskType.NUMERIC, "3", "x") is False
    assert evaluate_answer(TaskType.TEXT_MATCH, "Bratislava", " bratislava ") is True


def test_k04_student_submit_publishes_answer_evaluated(db_session):
    school_id, topic_id, student_id = _setup(db_session)
    sp = _sys(school_id)
    repo = K04Repository(db_session)
    bus = EventBus()
    seen = []
    bus.subscribe("AnswerEvaluated", lambda e: seen.append(e))
    svc = K04Service(db_session, event_bus=bus)

    mission = repo.create_mission(school_id=school_id, topic_id=topic_id, title="M", is_verification=False)
    task = repo.create_task(school_id=school_id, mission_id=mission.id, task_type=TaskType.CHOICE.value, prompt="1+1", expected_answer="2", order_index=1)
    db_session.commit()

    student = Principal(user_id=student_id, role=Role.STUDENT, school_id=school_id)
    attempt = svc.submit_attempt(student, task_id=task.id, student_user_id=student_id, answer="2")
    db_session.commit()
    assert attempt.is_correct is True
    assert len(seen) == 1
    assert seen[0].payload["is_verification"] is False
    assert seen[0].payload["correct"] is True
    assert seen[0].payload["attempt_ref"] == str(attempt.id)


def test_k04_submit_permissions_denied_for_other_student(db_session):
    school_id, topic_id, student_id = _setup(db_session)
    repo = K04Repository(db_session)
    mission = repo.create_mission(school_id=school_id, topic_id=topic_id, title="M", is_verification=True)
    task = repo.create_task(school_id=school_id, mission_id=mission.id, task_type=TaskType.TEXT_MATCH.value, prompt="p", expected_answer="ok")
    other = uuid.uuid4()
    db_session.add(User(id=other, school_id=school_id, username=f"o-{other}", full_name="O", password_hash="x"))
    db_session.commit()
    svc = K04Service(db_session, event_bus=EventBus())
    student = Principal(user_id=student_id, role=Role.STUDENT, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.submit_attempt(student, task_id=task.id, student_user_id=other, answer="ok")
