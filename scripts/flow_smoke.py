#!/usr/bin/env python3
"""F8.5: HTTP flow smoke test.
Spustí backend na voľnom porte s dočasnou SQLite DB, nasype demo dáta,
vykoná tok cez HTTP (čo je dostupné v aktuálnom API) a negatívne prípady,
server na konci zastaví. Výpis skutočných výsledkov.
Exit 0 iba ak všetky kontrolované kroky prejdú.
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PY = str(ROOT / "backend/.venv/bin/python")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_ready(base: str, proc: subprocess.Popen, timeout: float = 30.0) -> bool:
    import urllib.request, urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(base + "/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def http(method: str, base: str, path: str, token: str | None = None, json_body=None):
    import urllib.request, urllib.error
    url = base + path
    data = None
    headers = {}
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read()
            ct = r.headers.get("Content-Type", "")
            parsed = json.loads(body) if "json" in ct and body else body.decode(errors="ignore")
            return r.status, parsed
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body.decode(errors="ignore")
        return e.code, parsed
    except Exception as e:
        return None, str(e)


def seed_db(db_path: str, port: int) -> dict:
    """Seed demo-like users directly into temp DB for login (is_demo). Returns credentials."""
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env.setdefault("JWT_SECRET_KEY", "flow-smoke-secret-key-0123456789")
    env.setdefault("JWT_ALGORITHM", "HS256")
    env["PYTHONPATH"] = str(BACKEND)
    code = r'''
import os, sys, uuid
sys.path.insert(0, os.environ["PYTHONPATH"])
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database.session import Base
import app.core.audit.logger, app.core.events.bus
import app.shared.identity, app.shared.school, app.shared.curriculum
from app.core.security.auth import hash_password
from app.shared.identity import User, RoleAssignment, GuardianLink
from app.shared.school import School, SchoolYear, ClassGroup, Enrollment
from app.shared.curriculum import Subject, Topic
from app.shared.types import Role
from sqlalchemy import insert
from datetime import datetime, timezone
import json
db_url=os.environ["DATABASE_URL"]
engine=create_engine(db_url, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
S=sessionmaker(bind=engine)()
school_id=uuid.uuid4(); year_id=uuid.uuid4(); class_id=uuid.uuid4(); subject_id=uuid.uuid4(); topic_id=uuid.uuid4()
pw=hash_password("demo-password")
S.add(School(id=school_id,name="DEMO Flow School",is_demo=True))
S.add(SchoolYear(id=year_id,school_id=school_id,name="2026/27",is_demo=True))
S.add(ClassGroup(id=class_id,school_id=school_id,school_year_id=year_id,name="5A",grade=5,is_demo=True))
ids={}
for role in ["student","teacher","leadership","parent"]:
    uid=uuid.uuid4(); ids[role]=str(uid)
    uname=f"demo_{role}"
    S.add(User(id=uid,school_id=school_id,username=uname,full_name=f"DEMO {role}",password_hash=pw,is_demo=True))
    S.add(RoleAssignment(user_id=uid,school_id=school_id,role=getattr(Role,role.upper()).value,is_demo=True))
S.add(Enrollment(id=uuid.uuid4(),school_id=school_id,school_year_id=year_id,class_group_id=class_id,student_user_id=uuid.UUID(ids["student"]),is_demo=True))
S.add(GuardianLink(id=uuid.uuid4(),guardian_user_id=uuid.UUID(ids["parent"]),child_user_id=uuid.UUID(ids["student"]),school_id=school_id,relationship="demo",is_demo=True))
S.add(Subject(id=subject_id,school_id=school_id,name="DEMO Matematika",is_demo=True))
S.add(Topic(id=topic_id,school_id=school_id,subject_id=subject_id,name="DEMO Zlomky",grade=5,order_index=1,is_demo=True))
ct=Base.metadata.tables.get("school_class_teacher")
if ct is not None:
    S.execute(insert(ct).values(id=uuid.uuid4(),school_id=school_id,class_group_id=class_id,teacher_user_id=uuid.UUID(ids["teacher"]),valid_from=datetime.now(timezone.utc),valid_to=None,version=1,is_demo=True))
S.commit()
print(json.dumps({"school_id":str(school_id),"ids":ids,"usernames":{r:f"demo_{r}" for r in ids}}))
'''
    r = subprocess.run([PY, "-c", code], env=env, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise RuntimeError("seed failed")
    return json.loads(r.stdout.strip().splitlines()[-1])


def main() -> int:
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    tmp = tempfile.TemporaryDirectory(prefix="flow_smoke_")
    db_path = str(Path(tmp.name) / "smoke.db")
    log_path = str(Path(tmp.name) / "server.log")
    results = []
    failures = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {name}" + (f" :: {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["JWT_SECRET_KEY"] = "flow-smoke-secret-key-0123456789"
    env["JWT_ALGORITHM"] = "HS256"
    env["PYTHONPATH"] = str(BACKEND)

    # seed DB (creates schema+data)
    try:
        info = seed_db(db_path, port)
        check("seed_demo_data", True, f"school_id={info['school_id']} (is_demo)")
    except Exception as e:
        check("seed_demo_data", False, str(e))
        print("VYSLEDOK: FAIL (seed)")
        return 1

    logf = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen([PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
                            cwd=str(BACKEND), env=env, stdout=logf, stderr=subprocess.STDOUT)
    try:
        ready = wait_ready(base, proc)
        check("backend_start_/health", ready, base)
        if not ready:
            logf.flush()
            try:
                print(Path(log_path).read_text()[-2000:])
            except Exception:
                pass
            print("VYSLEDOK: FAIL (backend not ready)")
            return 1

        # login 4 roles
        tokens = {}
        for role in ["student", "teacher", "leadership", "parent"]:
            st, body = http("POST", base, "/auth/login", json_body={"username": f"demo_{role}", "password": "demo-password"})
            ok = st == 200 and isinstance(body, dict) and "access_token" in body
            tokens[role] = body.get("access_token") if ok else None
            check(f"login_{role}", ok, f"status={st}")

        # status endpoints reachable (HTTP smoke of available API)
        for path in ["/k04/status", "/k05/status", "/k03/status", "/k09/status", "/k12/status", "/k13/status"]:
            # try with and without auth; some may 404 if not in openapi
            st, body = http("GET", base, path)
            check(f"endpoint_{path}", st in (200, 401, 403, 404), f"status={st}")

        # Attempt core flow via HTTP as specified by 8.5 - document actual availability
        # submit answer (K-04) - no public HTTP endpoint in current API
        st, body = http("POST", base, "/k04/submit", token=tokens.get("student"), json_body={"answer": "2"})
        has_submit = st == 200
        check("http_student_submit_answer_k04", has_submit, f"status={st} body={body} (očakávané: endpoint nie je v OpenAPI/API -> medzera)")
        # K-05 state read
        st, body = http("GET", base, "/k05/state", token=tokens.get("student"))
        check("http_k05_state", st == 200, f"status={st} body={body} (medzera ak chýba endpoint)")
        # K-03 recommendation
        st, body = http("GET", base, "/k03/recommendation", token=tokens.get("student"))
        check("http_k03_recommendation", st == 200, f"status={st} body={body}")
        # K-09 teacher overview
        st, body = http("GET", base, "/k09/overview", token=tokens.get("teacher"))
        check("http_k09_teacher_overview", st == 200, f"status={st} body={body}")
        # K-12 analytics aggregate
        st, body = http("GET", base, "/analytics/overview", token=tokens.get("leadership"))
        check("http_k12_aggregate", st == 200, f"status={st} body={body}")
        # K-13 parent view
        st, body = http("GET", base, "/parent/overview", token=tokens.get("parent"))
        check("http_k13_parent_view", st == 200, f"status={st} body={body}")

        # audit verify - not exposed via HTTP; mark as gap
        check("http_audit_verify", False, "audit verify nie je vystavený cez HTTP endpoint (overené v integračných testoch)")

        # negative cases
        st, body = http("GET", base, "/health")  # public ok
        check("public_health", st == 200, f"status={st}")
        # without token - try an endpoint that would require auth if enforced
        st, body = http("GET", base, "/k01/status")
        # record actual behavior
        check("no_token_behavior_k01_status", st in (401, 200), f"status={st} (200 znamená verejný status endpoint bez auth)")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        logf.close()

    print("---SUMMARY---")
    for n, ok, d in results:
        print(f"{'OK' if ok else 'FAIL'}: {n}")
    if failures:
        print(f"VYSLEDOK: FAIL ({len(failures)} zlyhaní)")
        print("POZNAMKA: Tok 8.5 vyžaduje doménové HTTP endpointy (submit, stavy, prehľady, odporúčania, audit verify), ktoré v aktuálnom API/OpenAPI chýbajú (väčšina modulov má len /status alebo prázdny router). Medzery sú zaznamenané.")
        return 1
    print("VYSLEDOK: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
