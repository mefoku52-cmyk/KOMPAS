import os
import uuid
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:////data/data/com.termux/files/home/KOMPAS/.data/test_k18_ops.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-1234567890-1234567890")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert, select

from app.main import create_app
from app.core.database.session import Base, engine, SessionLocal
from app.core.security.auth import create_access_token
from app.shared.types import Role
from app.shared.identity import User
from app.shared.school import School, SchoolYear, ClassGroup, Enrollment
from app.modules.k18_intelligence.repository.models import ILDeadLetter, ILAudit, ILPerceptionEvent


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def mk_user(db, school_id, username):
    uid = uuid.uuid4()
    db.add(User(id=uid, school_id=school_id, username=username, full_name=username, password_hash="x", is_active=True))
    db.flush()
    return uid


def auth(user_id, role, school_id):
    return {"Authorization": f"Bearer {create_access_token(str(user_id), role, school_id)}"}


def seed():
    db = SessionLocal()
    try:
        school = uuid.uuid4()
        db.add(School(id=school, name=f"S-{school}"))
        year = uuid.uuid4(); cls = uuid.uuid4()
        db.add(SchoolYear(id=year, school_id=school, name="2026/27"))
        db.add(ClassGroup(id=cls, school_id=school, school_year_id=year, name="1A", grade=1))
        teacher = mk_user(db, school, "teacher")
        leader = mk_user(db, school, "leader")
        student = mk_user(db, school, "student")
        db.add(Enrollment(school_id=school, school_year_id=year, class_group_id=cls, student_user_id=student))
        ct = Base.metadata.tables["school_class_teacher"]
        db.execute(insert(ct).values(id=uuid.uuid4(), school_id=school, class_group_id=cls, teacher_user_id=teacher, valid_from=datetime.now(timezone.utc), valid_to=None, version=1, is_demo=False))
        db.commit()
        return {"school": school, "teacher": teacher, "leader": leader, "student": student}
    finally:
        db.close()


@pytest.fixture()
def ctx():
    setup_module()
    data = seed()
    app = create_app()
    with TestClient(app) as c:
        yield c, data


def test_integration_answerevaluated_maps_and_dedupes(ctx):
    client, d = ctx
    h = auth(d["teacher"], Role.TEACHER, d["school"])
    eid = str(uuid.uuid4())
    payload = {
        "event_type": "AnswerEvaluated",
        "event_id": eid,
        "source_module": "k04",
        "school_id": str(d["school"]),
        "student_user_id": str(d["student"]),
        "payload": {"correct": False, "time_taken_sec": 2},
    }
    r1 = client.post("/integration/events", headers=h, json=payload)
    assert r1.status_code == 200
    assert r1.json()["mapped_event_type"] == "mission_answer"
    r2 = client.post("/integration/events", headers=h, json=payload)
    assert r2.status_code == 200
    assert r2.json()["result"]["status"] == "duplicate"
    db = SessionLocal()
    try:
        count = db.execute(select(ILPerceptionEvent).where(ILPerceptionEvent.event_id == uuid.UUID(eid))).scalars().all()
        assert len(count) == 1
    finally:
        db.close()


def test_dlq_retry_requeues_and_audits(ctx):
    client, d = ctx
    h_lead = auth(d["leader"], Role.LEADERSHIP, d["school"])
    h_teacher = auth(d["teacher"], Role.TEACHER, d["school"])
    event_id = uuid.uuid4()
    db = SessionLocal()
    try:
        rec = ILDeadLetter(event_id=event_id, handler="k18.orchestrator", payload={"event_type": "mission_answer", "entity_type": "student", "entity_id": str(d["student"]), "correct": False, "time_taken_sec": 1}, error="boom", retry_count=3, last_attempt_at=datetime.now(timezone.utc), school_id=d["school"])
        db.add(rec)
        db.commit()
        dlq_id = str(rec.id)
    finally:
        db.close()

    assert client.get("/intelligence/ops/dlq", headers=h_teacher).status_code == 403
    r = client.get("/intelligence/ops/dlq", headers=h_lead)
    assert r.status_code == 200
    assert any(i["id"] == dlq_id for i in r.json()["items"])

    retry = client.post(f"/intelligence/ops/dlq/{dlq_id}/retry", headers=h_lead)
    assert retry.status_code == 200
    assert retry.json()["requeued_event_id"] == str(event_id)

    db = SessionLocal()
    try:
        assert db.get(ILDeadLetter, uuid.UUID(dlq_id)) is None
        audits = db.execute(select(ILAudit).where(ILAudit.action == "ops.dlq.retry")).scalars().all()
        assert any(str(event_id) in str(a.details) for a in audits)
    finally:
        db.close()

    proc = client.post("/intelligence/ops/process-once?limit=20", headers=h_lead)
    assert proc.status_code == 200
    assert proc.json()["claimed"] >= 1


def test_integration_event_rejects_cross_school_and_foreign_entity(ctx):
    client, d = ctx
    h_teacher = auth(d["teacher"], Role.TEACHER, d["school"])
    other_school = uuid.uuid4()
    other_student = uuid.uuid4()

    # cross-school spoof
    r1 = client.post("/integration/events", headers=h_teacher, json={
        "event_type": "AnswerEvaluated", "event_id": str(uuid.uuid4()),
        "source_module": "k04", "school_id": str(other_school),
        "student_user_id": str(d["student"]),
        "payload": {"correct": False, "time_taken_sec": 2},
    })
    assert r1.status_code == 403

    # foreign entity in same school but not taught
    r2 = client.post("/integration/events", headers=h_teacher, json={
        "event_type": "AnswerEvaluated", "event_id": str(uuid.uuid4()),
        "source_module": "k04", "school_id": str(d["school"]),
        "student_user_id": str(other_student),
        "payload": {"correct": False, "time_taken_sec": 2},
    })
    assert r2.status_code == 403

    db = SessionLocal()
    try:
        denied = db.execute(select(ILAudit).where(ILAudit.action == "integration.denied")).scalars().all()
        assert len(denied) >= 2
    finally:
        db.close()
