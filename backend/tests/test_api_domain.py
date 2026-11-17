from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert

from app.core.database.session import Base, get_db
from app.core.security.auth import create_access_token
from app.shared.curriculum import Subject, Topic
from app.shared.identity import GuardianLink, RoleAssignment, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Role


def _seed(db) -> dict:
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    ids = {role: uuid.uuid4() for role in ("student", "teacher", "leadership", "parent")}

    db.add(School(id=school_id, name=f"APISchool-{school_id}", is_demo=True))
    db.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27", is_demo=True))
    db.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="5A", grade=5, is_demo=True))
    db.add(Subject(id=subject_id, school_id=school_id, name=f"Matematika-{subject_id}", is_demo=True))
    db.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name="Zlomky", grade=5, order_index=1, is_demo=True))
    for role, user_id in ids.items():
        db.add(User(id=user_id, school_id=school_id, username=f"api-{role}-{user_id}", full_name=f"Demo {role}", password_hash="x", is_demo=True))
        db.add(RoleAssignment(id=uuid.uuid4(), user_id=user_id, school_id=school_id, role=getattr(Role, role.upper()).value, is_demo=True))
    db.add(Enrollment(id=uuid.uuid4(), school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=ids["student"], is_demo=True))
    db.add(GuardianLink(id=uuid.uuid4(), guardian_user_id=ids["parent"], child_user_id=ids["student"], school_id=school_id, relationship="demo", is_demo=True))
    ct = Base.metadata.tables["school_class_teacher"]
    db.execute(insert(ct).values(
        id=uuid.uuid4(), school_id=school_id, class_group_id=class_id,
        teacher_user_id=ids["teacher"], valid_from=datetime.now(timezone.utc),
        valid_to=None, version=1, is_demo=True,
    ))
    db.commit()
    tokens = {
        role: create_access_token(user_id, getattr(Role, role.upper()), school_id)
        for role, user_id in ids.items()
    }
    return {
        "school_id": school_id, "year_id": year_id, "class_id": class_id,
        "subject_id": subject_id, "topic_id": topic_id, "ids": ids, "tokens": tokens,
    }


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def api(db_session, monkeypatch):
    import app.modules.k05_knowledge_continuity.events.handlers as k05_handlers

    monkeypatch.setattr(k05_handlers, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    ctx = _seed(db_session)
    yield client, ctx
    app.dependency_overrides.clear()


def test_status_requires_authentication(api):
    client, _ = api
    assert client.get("/k01/status").status_code == 401
    assert client.get("/k04/status", headers=_headers(_seed_token())).status_code == 401


def _seed_token() -> str:
    return "invalid-token"


def test_k01_profile_and_history(api):
    client, ctx = api
    leader = _headers(ctx["tokens"]["leadership"])
    created = client.post("/k01/profiles", headers=leader, json={
        "student_user_id": str(ctx["ids"]["student"]),
        "school_year_id": str(ctx["year_id"]),
        "grade": 5,
        "purpose": "individual_progress",
        "is_demo": True,
    })
    assert created.status_code == 200, created.text
    assert created.json()["grade"] == 5

    history = client.get(
        f"/k01/profiles/{ctx['ids']['student']}/history",
        headers=_headers(ctx["tokens"]["student"]),
    )
    assert history.status_code == 200, history.text
    body = history.json()
    assert body["total"] == 1
    assert body["items"][0]["grade"] == 5
    assert body["limit"] == 50


def test_k02_workspace_tree(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    ws = client.post("/k02/workspaces", headers=teacher, json={
        "subject_id": str(ctx["subject_id"]),
        "teacher_user_id": str(ctx["ids"]["teacher"]),
        "name": "Matematika 5",
        "is_demo": True,
    })
    assert ws.status_code == 200, ws.text
    workspace_id = ws.json()["id"]

    listing = client.get(f"/k02/workspaces?teacher_user_id={ctx['ids']['teacher']}", headers=teacher)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    node = client.post(f"/k02/workspaces/{workspace_id}/nodes", headers=teacher, json={
        "title": "Zlomky - uvod",
        "topic_id": str(ctx["topic_id"]),
        "is_demo": True,
    })
    assert node.status_code == 200, node.text

    nodes = client.get(f"/k02/workspaces/{workspace_id}/nodes", headers=teacher)
    assert nodes.status_code == 200
    assert nodes.json()["total"] == 1


def test_k03_recommendation_after_practice(api):
    client, ctx = api
    student = _headers(ctx["tokens"]["student"])
    state = client.post("/k05/states", headers=student, json={
        "student_user_id": str(ctx["ids"]["student"]),
        "topic_id": str(ctx["topic_id"]),
        "kind": "practiced",
        "status": "in_progress_practice",
        "evidence_attempt_ref": str(uuid.uuid4()),
        "is_demo": True,
    })
    assert state.status_code == 200, state.text

    recs = client.get(
        f"/k03/recommendations/{ctx['ids']['student']}?persist=false",
        headers=student,
    )
    assert recs.status_code == 200, recs.text
    body = recs.json()
    assert body["total"] >= 1
    assert body["items"][0]["suggested_action"] == "practice"
    assert "Deterministic" in body["items"][0]["reason"]


def test_k04_mission_task_attempt(api):
    client, ctx = api
    leader = _headers(ctx["tokens"]["leadership"])
    student = _headers(ctx["tokens"]["student"])
    mission = client.post("/k04/missions", headers=leader, json={
        "topic_id": str(ctx["topic_id"]),
        "title": "Misia zlomky",
        "is_demo": True,
    })
    assert mission.status_code == 200, mission.text
    mission_id = mission.json()["id"]

    task = client.post(f"/k04/missions/{mission_id}/tasks", headers=leader, json={
        "task_type": "choice",
        "prompt": "1+1?",
        "expected_answer": "2",
        "is_demo": True,
    })
    assert task.status_code == 200, task.text
    task_id = task.json()["id"]

    tasks = client.get(f"/k04/missions/{mission_id}/tasks", headers=student)
    assert tasks.status_code == 200, tasks.text
    assert tasks.json()["total"] == 1

    attempt = client.post("/k04/attempts", headers=student, json={
        "task_id": task_id,
        "answer": "2",
        "is_demo": True,
    })
    assert attempt.status_code == 200, attempt.text
    assert attempt.json()["is_correct"] is True


def test_k05_state_self_and_forbidden_cross_student(api):
    client, ctx = api
    student = _headers(ctx["tokens"]["student"])
    state = client.post("/k05/states", headers=student, json={
        "student_user_id": str(ctx["ids"]["student"]),
        "topic_id": str(ctx["topic_id"]),
        "kind": "practiced",
        "status": "in_progress_practice",
        "is_demo": True,
    })
    assert state.status_code == 200, state.text
    rows = client.get(f"/k05/states/{ctx['ids']['student']}", headers=student)
    assert rows.status_code == 200
    assert rows.json()["total"] == 1

    other = client.get(f"/k05/states/{uuid.uuid4()}", headers=student)
    assert other.status_code in (403,), other.text


def test_k06_lab_definitions_and_simulation(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    defs = client.get("/lab/definitions", headers=teacher)
    assert defs.status_code == 200, defs.text
    items = defs.json()["items"]
    assert items and items[0]["compute_key"] == "ohms_law"
    definition_id = items[0]["id"]

    run = client.post("/lab/simulations", headers=teacher, json={
        "definition_id": definition_id,
        "inputs": {"resistance": 2, "current": 3},
        "is_demo": True,
    })
    assert run.status_code == 200, run.text
    assert run.json()["outputs"]["voltage"] == 6.0


def test_list_limit_upper_bound(api):
    client, ctx = api
    response = client.get(
        f"/k01/profiles/{ctx['ids']['student']}/history?limit=1000",
        headers=_headers(ctx["tokens"]["student"]),
    )
    assert response.status_code == 422


def test_k07_library_lifecycle(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    item = client.post("/k07/items", headers=teacher, json={"title": "Priprava", "is_demo": True})
    assert item.status_code == 200, item.text
    item_id = item.json()["id"]
    version = client.post(f"/k07/items/{item_id}/versions", headers=teacher, json={
        "version_number": 1, "content_text": "Obsah", "is_demo": True,
    })
    assert version.status_code == 200, version.text
    tag = client.post(f"/k07/items/{item_id}/tags", headers=teacher, json={"tag": "zlomky", "is_demo": True})
    assert tag.status_code == 200, tag.text
    listing = client.get("/k07/items", headers=teacher)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    versions = client.get(f"/k07/items/{item_id}/versions", headers=teacher)
    assert versions.status_code == 200
    assert versions.json()["total"] == 1


def test_k08_assistant_approval_flow(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    draft = client.post("/k08/drafts", headers=teacher, json={
        "title": "Plan hodiny", "draft_type": "lesson_plan", "topics": ["Zlomky"], "is_demo": True,
    })
    assert draft.status_code == 200, draft.text
    draft_id = draft.json()["id"]
    submit = client.post(f"/k08/drafts/{draft_id}/submit", headers=teacher)
    assert submit.status_code == 200, submit.text
    approve = client.post(f"/k08/drafts/{draft_id}/approve", headers=teacher)
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "approved"
    listing = client.get("/k08/drafts", headers=teacher)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_k09_class_overview(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    overview = client.get(f"/k09/classes/{ctx['class_id']}/overview", headers=teacher)
    assert overview.status_code == 200, overview.text
    assert overview.json()["total_students"] == 1

    student = _headers(ctx["tokens"]["student"])
    denied = client.get(f"/k09/classes/{ctx['class_id']}/overview", headers=student)
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "forbidden"


def test_k10_organization_tasks_and_plans(api):
    client, ctx = api
    leader = _headers(ctx["tokens"]["leadership"])
    task = client.post("/k10/tasks", headers=leader, json={"title": "Objednat pomocky", "is_demo": True})
    assert task.status_code == 200, task.text
    task_id = task.json()["id"]
    plan = client.post("/k10/plans", headers=leader, json={"name": "Plan skoly", "is_demo": True})
    assert plan.status_code == 200, plan.text
    assignment = client.post(f"/k10/tasks/{task_id}/assignments", headers=leader, json={
        "assignee_user_id": str(ctx["ids"]["teacher"]), "role_in_task": "solver", "is_demo": True,
    })
    assert assignment.status_code == 200, assignment.text
    tasks = client.get("/k10/tasks", headers=leader)
    assert tasks.status_code == 200
    assert tasks.json()["total"] == 1
    plans = client.get("/k10/plans", headers=leader)
    assert plans.status_code == 200
    assert plans.json()["total"] == 1


def test_k11_operations_state_machine(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    leader = _headers(ctx["tokens"]["leadership"])
    req = client.post("/k11/requests", headers=teacher, json={
        "request_type": "equipment", "title": "Projektor", "is_demo": True,
    })
    assert req.status_code == 200, req.text
    request_id = req.json()["id"]
    applied = client.post(f"/k11/requests/{request_id}/transition", headers=leader, json={"new_status": "approved"})
    assert applied.status_code == 200, applied.text
    invalid = client.post(f"/k11/requests/{request_id}/transition", headers=leader, json={"new_status": "fulfilled"})
    assert invalid.status_code == 400
    assert invalid.json()["error"]["message_key"] == "invalid_transition"
    listing = client.get("/k11/requests", headers=leader)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_k12_analytics_and_individual_purpose(api):
    client, ctx = api
    leader = _headers(ctx["tokens"]["leadership"])
    overview = client.get("/analytics/overview", headers=leader)
    assert overview.status_code == 200, overview.text
    assert overview.json()["suppressed"] is True

    no_purpose = client.get(f"/analytics/students/{ctx['ids']['student']}", headers=leader)
    assert no_purpose.status_code == 400
    with_purpose = client.get(
        f"/analytics/students/{ctx['ids']['student']}?purpose=individual_progress",
        headers=leader,
    )
    assert with_purpose.status_code == 200, with_purpose.text
    assert with_purpose.json()["student_user_id"] == str(ctx["ids"]["student"])


def test_k13_parent_center(api):
    client, ctx = api
    parent = _headers(ctx["tokens"]["parent"])
    children = client.get("/parent/children", headers=parent)
    assert children.status_code == 200, children.text
    assert children.json()["total"] == 1
    overview = client.get(f"/parent/children/{ctx['ids']['student']}", headers=parent)
    assert overview.status_code == 200, overview.text
    assert overview.json()["teacher_notes"] == []

    teacher = _headers(ctx["tokens"]["teacher"])
    denied = client.get("/parent/children", headers=teacher)
    assert denied.status_code == 403


def test_k14_communication_participants_only(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    parent = _headers(ctx["tokens"]["parent"])
    thread = client.post("/communication/threads", headers=teacher, json={
        "subject": "Dohoda o konzultacii",
        "participant_user_ids": [str(ctx["ids"]["parent"])],
        "is_private": True,
        "is_demo": True,
    })
    assert thread.status_code == 200, thread.text
    thread_id = thread.json()["id"]
    message = client.post(f"/communication/threads/{thread_id}/messages", headers=parent, json={
        "body": "Dakujem", "is_demo": True,
    })
    assert message.status_code == 200, message.text
    messages = client.get(f"/communication/threads/{thread_id}/messages", headers=teacher)
    assert messages.status_code == 200
    assert messages.json()["total"] == 1

    student = _headers(ctx["tokens"]["student"])
    denied = client.get(f"/communication/threads/{thread_id}/messages", headers=student)
    assert denied.status_code == 403


def test_k15_projects_flow(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    project = client.post("/projects", headers=teacher, json={
        "title": "Projekt zlomky", "member_user_ids": [str(ctx["ids"]["student"])], "is_demo": True,
    })
    assert project.status_code == 200, project.text
    project_id = project.json()["id"]
    task = client.post(f"/projects/{project_id}/tasks", headers=teacher, json={
        "title": "Vytvorit plakat", "assignee_user_id": str(ctx["ids"]["student"]), "is_demo": True,
    })
    assert task.status_code == 200, task.text
    task_id = task.json()["id"]
    submission = client.post(f"/projects/tasks/{task_id}/submissions", headers=teacher, json={
        "content": "Hotovo", "is_demo": True,
    })
    assert submission.status_code == 200, submission.text
    tasks = client.get(f"/projects/{project_id}/tasks", headers=teacher)
    assert tasks.status_code == 200
    assert tasks.json()["total"] == 1
    submissions = client.get(f"/projects/tasks/{task_id}/submissions", headers=teacher)
    assert submissions.status_code == 200
    assert submissions.json()["total"] == 1


def test_k16_knowledge_context_and_audit(api):
    client, ctx = api
    leader = _headers(ctx["tokens"]["leadership"])
    source = client.post("/k16/sources", headers=leader, json={
        "name": "Standard", "source_type": "standard", "content": "Zlomky a desatinne cisla", "approved": True,
    })
    assert source.status_code == 200, source.text
    search = client.get("/k16/knowledge?q=zlomky", headers=leader)
    assert search.status_code == 200, search.text
    assert search.json()["total"] == 1

    memory = client.post("/k16/context-memory", headers=leader, json={
        "source_record_ref": "source:1", "content": "Kontext k zlomkom",
    })
    assert memory.status_code == 200, memory.text
    memories = client.get("/k16/context-memory", headers=leader)
    assert memories.status_code == 200
    assert memories.json()["total"] == 1

    run = client.post("/k16/orchestrator/run", headers=leader, json={
        "task": "work_assistant", "prompt": "Navrhni cvicenie", "payload": {"topic_name": "Zlomky"},
    })
    assert run.status_code == 200, run.text
    assert run.json()["output"].startswith("[null:")
    assert run.json()["external_calls"] is False

    report = client.get("/k16/audit/report", headers=leader)
    assert report.status_code == 200, report.text
    assert report.json()["total"] >= 1


def test_error_format_contains_request_id(api):
    client, _ = api
    response = client.get(f"/parent/children/{uuid.uuid4()}", headers=_headers("bad-token"))
    assert response.status_code == 401
    body = response.json()["error"]
    assert body["code"] == "unauthorized"
    assert body["message_key"] == "invalid_token"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_list_pagination_and_parameter_bounds(api):
    client, ctx = api
    teacher = _headers(ctx["tokens"]["teacher"])
    for title in ("Prvý", "Druhý"):
        created = client.post("/k07/items", headers=teacher, json={"title": title, "is_demo": True})
        assert created.status_code == 200, created.text
    window = client.get("/k07/items?limit=1&offset=1", headers=teacher)
    assert window.status_code == 200, window.text
    body = window.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["items"]) == 1
    assert client.get("/k07/items?limit=0", headers=teacher).status_code == 422
    assert client.get("/k07/items?offset=-1", headers=teacher).status_code == 422
