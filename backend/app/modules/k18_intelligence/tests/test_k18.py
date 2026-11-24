import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:////data/data/com.termux/files/home/KOMPAS/.data/test_k18.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-1234567890-1234567890")

from fastapi.testclient import TestClient
from app.main import create_app
from app.core.database.session import Base, engine, SessionLocal
from app.core.security.auth import create_access_token
from app.shared.types import Role
from app.shared.identity import RoleAssignment
from app.shared.identity import User
from app.shared.school import School


def setup_module():
    Base.metadata.create_all(bind=engine)


def auth(role=Role.TEACHER, school_id=None, user_id=None):
    uid = user_id or uuid.uuid4()
    sid = school_id or uuid.uuid4()
    db = SessionLocal()
    try:
        if not db.get(School, sid):
            db.add(School(id=sid, name=f"School-{sid}"))
            db.flush()
        if not db.get(User, uid):
            db.add(User(id=uid, school_id=sid, username=f"u-{uid}", full_name="Test", password_hash="x", is_active=True))
            db.flush()
        if not db.query(RoleAssignment).filter_by(user_id=uid, school_id=sid, role=role.value).first():
            db.add(RoleAssignment(user_id=uid, school_id=sid, role=role.value))
        db.commit()
    finally:
        db.close()
    token = create_access_token(str(uid), role, sid)
    return {"Authorization": f"Bearer {token}"}, uid, sid


def test_k18_status_and_ingest():
    app = create_app()
    client = TestClient(app)
    headers, _, _ = auth()
    r = client.get("/intelligence/status")
    assert r.status_code == 200
    r = client.post("/intelligence/events", headers=headers, json={"event_type": "mission_answer", "payload": {"entity_type": "student", "entity_id": "S1", "correct": False, "time_taken_sec": 2}})
    assert r.status_code == 403


def test_k18_duplicate_event_id():
    app = create_app()
    client = TestClient(app)
    headers, _, _ = auth()
    eid = str(uuid.uuid4())
    body = {"event_type": "mission_answer", "event_id": eid, "payload": {"entity_type": "student", "entity_id": "S2", "correct": False, "time_taken_sec": 2}}
    r1 = client.post("/intelligence/events", headers=headers, json=body)
    r2 = client.post("/intelligence/events", headers=headers, json=body)
    assert r1.status_code == 403
    assert r2.status_code == 403
