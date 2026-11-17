import uuid

import pytest

from app.modules.k05_knowledge_continuity.domain.models import TopicProgressKind, TopicProgressStatus
from app.modules.k05_knowledge_continuity.events.handlers import handle_answer_evaluated
from app.modules.k05_knowledge_continuity.services.service import K05Service
from app.core.events.bus import DomainEvent
from app.shared.curriculum import Subject, Topic
from app.shared.identity import GuardianLink, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role, system_principal


def _setup(db_session):
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    student_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    leader_id = uuid.uuid4()
    class_id = uuid.uuid4()

    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.flush()
    db_session.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27"))
    db_session.add(User(id=student_id, school_id=school_id, username=f"st-{student_id}", full_name="S", password_hash="x"))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(User(id=parent_id, school_id=school_id, username=f"p-{parent_id}", full_name="P", password_hash="x"))
    db_session.add(User(id=leader_id, school_id=school_id, username=f"l-{leader_id}", full_name="L", password_hash="x"))
    db_session.add(Subject(id=subject_id, school_id=school_id, name="Math"))
    db_session.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name="Fractions", grade=5, order_index=1))
    db_session.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="5A", grade=5))
    db_session.flush()
    db_session.add(Enrollment(school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=student_id))
    db_session.flush()
    db_session.add(GuardianLink(guardian_user_id=parent_id, child_user_id=student_id, school_id=school_id))
    db_session.commit()
    return dict(school_id=school_id, topic_id=topic_id, student_id=student_id, teacher_id=teacher_id, parent_id=parent_id, leader_id=leader_id, class_id=class_id)


def _sys(school_id):
    p = system_principal()
    return Principal(user_id=p.user_id, role=None, school_id=school_id, scopes=p.scopes, is_system=True)


def test_k05_verified_mastery_requires_verification_evidence(db_session):
    ctx = _setup(db_session)
    svc = K05Service(db_session)
    sp = _sys(ctx["school_id"])
    # cannot get verified mastery from practice-only evidence
    with pytest.raises(ValueError):
        svc.record_state(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], topic_id=ctx["topic_id"],
                         kind=TopicProgressKind.PRACTICED, status=TopicProgressStatus.VERIFIED_MASTERY,
                         evidence_attempt_ref="p1", is_verification_evidence=False)
    # verified mastery requires verification evidence
    with pytest.raises(ValueError):
        svc.record_state(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], topic_id=ctx["topic_id"],
                         kind=TopicProgressKind.VERIFIED, status=TopicProgressStatus.VERIFIED_MASTERY,
                         evidence_attempt_ref=None, is_verification_evidence=True)
    ok = svc.record_state(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], topic_id=ctx["topic_id"],
                          kind=TopicProgressKind.VERIFIED, status=TopicProgressStatus.VERIFIED_MASTERY,
                          evidence_attempt_ref="exam-1", is_verification_evidence=True)
    db_session.commit()
    assert ok.status == TopicProgressStatus.VERIFIED_MASTERY.value


def test_k05_student_can_record_practice_but_not_verified(db_session):
    ctx = _setup(db_session)
    svc = K05Service(db_session)
    student = Principal(user_id=ctx["student_id"], role=Role.STUDENT, school_id=ctx["school_id"])
    p = svc.record_state(student, school_id=ctx["school_id"], student_user_id=ctx["student_id"], topic_id=ctx["topic_id"],
                         kind=TopicProgressKind.PRACTICED, status=TopicProgressStatus.IN_PROGRESS_PRACTICE,
                         evidence_attempt_ref="a1", is_verification_evidence=False)
    assert p.kind == TopicProgressKind.PRACTICED.value
    with pytest.raises(PermissionError):
        svc.record_state(student, school_id=ctx["school_id"], student_user_id=ctx["student_id"], topic_id=ctx["topic_id"],
                         kind=TopicProgressKind.VERIFIED, status=TopicProgressStatus.VERIFIED_MASTERY,
                         evidence_attempt_ref="v1", is_verification_evidence=True)


def test_k05_permissions_and_history(db_session):
    ctx = _setup(db_session)
    svc = K05Service(db_session)
    sp = _sys(ctx["school_id"])
    svc.record_state(sp, school_id=ctx["school_id"], student_user_id=ctx["student_id"], topic_id=ctx["topic_id"],
                     kind=TopicProgressKind.COVERED, status=TopicProgressStatus.PARTIALLY_MASTERED, evidence_attempt_ref="c1")
    db_session.commit()
    student = Principal(user_id=ctx["student_id"], role=Role.STUDENT, school_id=ctx["school_id"])
    assert len(svc.list_states(student, student_user_id=ctx["student_id"], school_id=ctx["school_id"])) == 1
    parent = Principal(user_id=ctx["parent_id"], role=Role.PARENT, school_id=ctx["school_id"])
    assert len(svc.list_states(parent, student_user_id=ctx["student_id"], school_id=ctx["school_id"])) == 1
    teacher = Principal(user_id=ctx["teacher_id"], role=Role.TEACHER, school_id=ctx["school_id"])
    assert len(svc.list_states(teacher, student_user_id=ctx["student_id"], school_id=ctx["school_id"], class_group_id=ctx["class_id"], teaches=True)) == 1
    with pytest.raises(PermissionError):
        svc.list_states(teacher, student_user_id=ctx["student_id"], school_id=ctx["school_id"], class_group_id=ctx["class_id"], teaches=False)
    leader = Principal(user_id=ctx["leader_id"], role=Role.LEADERSHIP, school_id=ctx["school_id"])
    assert len(svc.list_states(leader, student_user_id=ctx["student_id"], school_id=ctx["school_id"], purpose="support")) == 1
    with pytest.raises(PermissionError):
        svc.list_states(leader, student_user_id=ctx["student_id"], school_id=ctx["school_id"], purpose="")


def test_k05_handle_answer_evaluated_practice_and_verification(db_session, monkeypatch):
    ctx = _setup(db_session)
    # monkeypatch handler SessionLocal to use same db session and avoid closing fixture session
    import app.modules.k05_knowledge_continuity.events.handlers as handlers
    monkeypatch.setattr(handlers, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    evt_practice = DomainEvent(event_type="AnswerEvaluated", school_id=ctx["school_id"], payload={
        "student_user_id": ctx["student_id"], "topic_id": ctx["topic_id"], "attempt_ref": "p1", "is_verification": False, "correct": True
    })
    handle_answer_evaluated(evt_practice)
    db_session.commit()
    svc = K05Service(db_session)
    sp = _sys(ctx["school_id"])
    rows = svc.list_states(sp, student_user_id=ctx["student_id"], school_id=ctx["school_id"])
    assert any(r.kind == TopicProgressKind.PRACTICED.value and r.status == TopicProgressStatus.PARTIALLY_MASTERED.value for r in rows)
    assert not any(r.status == TopicProgressStatus.VERIFIED_MASTERY.value for r in rows)

    evt_verify = DomainEvent(event_type="AnswerEvaluated", school_id=ctx["school_id"], payload={
        "student_user_id": ctx["student_id"], "topic_id": ctx["topic_id"], "attempt_ref": "v1", "is_verification": True, "correct": True
    })
    handle_answer_evaluated(evt_verify)
    db_session.commit()
    rows2 = svc.list_states(sp, student_user_id=ctx["student_id"], school_id=ctx["school_id"])
    assert any(r.kind == TopicProgressKind.VERIFIED.value and r.status == TopicProgressStatus.VERIFIED_MASTERY.value and r.is_verification_evidence for r in rows2)
