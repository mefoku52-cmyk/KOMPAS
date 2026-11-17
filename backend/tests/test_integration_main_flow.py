import uuid
from datetime import datetime, timezone

from sqlalchemy import insert

from app.core.audit.logger import verify_chain
from app.core.database.session import Base
from app.core.events.bus import EventBus
from app.modules.k03_adaptive_learning.services.service import K03Service
from app.modules.k04_missions.services.service import K04Service
from app.modules.k05_knowledge_continuity.events.handlers import register as register_k05
from app.modules.k05_knowledge_continuity.services.service import K05Service
from app.modules.k09_class_overview.services.service import K09Service
from app.modules.k12_analytics_center.services.service import K12Service
from app.shared.curriculum import Subject, Topic
from app.shared.identity import User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role


def _seed(db, *, students_n=5):
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    leader_id = uuid.uuid4()
    sys_p = Principal(user_id=uuid.uuid4(), role=None, school_id=school_id, scopes=(), is_system=True)

    db.add(School(id=school_id, name=f"DemoSchool-{school_id}", is_demo=True))
    db.flush()
    db.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27", is_demo=True))
    db.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="5A", grade=5, is_demo=True))
    db.add(User(id=teacher_id, school_id=school_id, username=f"teach-{teacher_id}", full_name="Demo Teacher", password_hash="x", is_demo=True))
    db.add(User(id=leader_id, school_id=school_id, username=f"lead-{leader_id}", full_name="Demo Leader", password_hash="x", is_demo=True))
    db.add(Subject(id=subject_id, school_id=school_id, name="Math", is_demo=True))
    db.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name="Zlomky", grade=5, order_index=1, is_demo=True))

    db.flush()
    ct = Base.metadata.tables["school_class_teacher"]
    db.execute(insert(ct).values(
        id=uuid.uuid4(), school_id=school_id, class_group_id=class_id, teacher_user_id=teacher_id,
        valid_from=datetime.now(timezone.utc), valid_to=None, version=1, is_demo=True,
    ))

    student_ids = []
    for i in range(students_n):
        sid = uuid.uuid4()
        db.add(User(id=sid, school_id=school_id, username=f"stud-{i}-{sid}", full_name=f"Demo Student {i}", password_hash="x", is_demo=True))
        db.add(Enrollment(id=uuid.uuid4(), school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=sid, is_demo=True))
        student_ids.append(sid)
    db.commit()
    return {
        "school_id": school_id, "class_id": class_id, "topic_id": topic_id,
        "teacher_id": teacher_id, "leader_id": leader_id, "student_ids": student_ids, "sys_p": sys_p,
    }


def test_main_event_flow_end_to_end(db_session, monkeypatch):
    import app.modules.k05_knowledge_continuity.events.handlers as k05_handlers

    # route handler SessionLocal to test session
    monkeypatch.setattr(k05_handlers, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    bus = EventBus()
    register_k05(bus)

    ctx = _seed(db_session, students_n=5)
    school_id = ctx["school_id"]
    class_id = ctx["class_id"]
    topic_id = ctx["topic_id"]
    sys_p = ctx["sys_p"]
    student_id = ctx["student_ids"][0]

    # 1) create mission/task (K04)
    k04 = K04Service(db_session, event_bus=bus)
    mission = k04.create_mission(sys_p, school_id=school_id, topic_id=topic_id, title="Misia zlomky", is_verification=False, is_demo=True)
    task = k04.repo.create_task(school_id=school_id, mission_id=mission.id, task_type="choice", prompt="1+1?", expected_answer="2", order_index=1, is_demo=True)
    db_session.commit()

    # 2) student solves task -> evaluation + event AnswerEvaluated -> K05 handler stores state
    student_p = Principal(user_id=student_id, role=Role.STUDENT, school_id=school_id)
    attempt = k04.submit_attempt(student_p, task_id=task.id, student_user_id=student_id, answer="2", is_demo=True)
    db_session.commit()

    assert attempt.is_correct is True
    assert attempt.evaluated is True

    # 3) personal progress (K05) - practiced/partially mastered recorded from practice event (not verified mastery)
    k05 = K05Service(db_session)
    states = k05.list_states(student_p, student_user_id=student_id, school_id=school_id)
    assert any(s.status == "partially_mastered" and s.kind == "practiced" for s in states)
    assert not any(s.status == "verified_mastery" for s in states)

    # give another student in-progress practice to drive recommendation
    other_id = ctx["student_ids"][1]
    k05.record_state(
        sys_p, school_id=school_id, student_user_id=other_id, topic_id=topic_id,
        kind="practiced", status="in_progress_practice", evidence_attempt_ref=str(uuid.uuid4()),
        is_verification_evidence=False, is_demo=True,
    )
    db_session.commit()

    # 4) adaptive recommendation (K03) - deterministic, explainable, suggestion not auto-applied
    k03 = K03Service(db_session)
    other_p = Principal(user_id=other_id, role=Role.STUDENT, school_id=school_id)
    recs = k03.recommend_for_student(other_p, school_id=school_id, student_user_id=other_id)
    assert len(recs) >= 1
    assert "reason" in recs[0] and recs[0]["suggested_action"] == "practice"
    assert "Deterministic" in recs[0]["reason"]

    # 5) class overview for teacher (K09)
    teacher_p = Principal(user_id=ctx["teacher_id"], role=Role.TEACHER, school_id=school_id)
    k09 = K09Service(db_session)
    overview = k09.get_class_overview(teacher_p, school_id=school_id, class_group_id=class_id)
    assert overview["total_students"] == 5
    assert overview["tracked_student_topic_pairs"] >= 2

    # 6) school analytics (K12) aggregates, not suppressed at >=5
    leader_p = Principal(user_id=ctx["leader_id"], role=Role.LEADERSHIP, school_id=school_id)
    k12 = K12Service(db_session)
    agg = k12.get_school_overview(leader_p, school_id=school_id)
    assert agg["suppressed"] is False
    assert agg["total_students"] == 5

    # 7) audit chain valid after flow
    ok, bad_id = verify_chain(db_session)
    assert ok is True
    assert bad_id is None
