#!/usr/bin/env python3
"""
Demonštračné dáta pre KOMPAS (ilustračné, nie skutočné osobné údaje).
Všetky záznamy sú označené is_demo = true.

Spustenie (z koreňa repozitára):
  set -a; . ./.env; set +a
  PYTHONPATH=backend backend/.venv/bin/python scripts/seed_demo.py
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# load .env if present
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)

os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT}/.data/kompas.db")

from sqlalchemy import insert, select  # noqa: E402

from app.core.database.session import Base, SessionLocal, engine  # noqa: E402
import app.core.audit.logger  # noqa: F401,E402
import app.core.events.bus  # noqa: F401,E402
import app.shared.identity  # noqa: F401,E402
import app.shared.school  # noqa: F401,E402
import app.shared.curriculum  # noqa: F401,E402
import app.modules.k01_learning_profile.domain.models  # noqa: F401,E402
import app.modules.k02_subject_workspace.domain.models  # noqa: F401,E402
import app.modules.k03_adaptive_learning.domain.models  # noqa: F401,E402
import app.modules.k04_missions.domain.models  # noqa: F401,E402
import app.modules.k05_knowledge_continuity.domain.models  # noqa: F401,E402
import app.modules.k06_virtual_lab.domain.models  # noqa: F401,E402
import app.modules.k07_professional_library.domain.models  # noqa: F401,E402
import app.modules.k08_work_assistant.domain.models  # noqa: F401,E402
import app.modules.k09_class_overview.domain.models  # noqa: F401,E402
import app.modules.k10_organization_center.domain.models  # noqa: F401,E402
import app.modules.k11_operations_center.domain.models  # noqa: F401,E402
import app.modules.k12_analytics_center.domain.models  # noqa: F401,E402
import app.modules.k14_communication_center.domain.models  # noqa: F401,E402
import app.modules.k15_collaboration_projects.domain.models  # noqa: F401,E402
import app.modules.k16_intelligent_core.domain.models  # noqa: F401,E402

from app.core.security.auth import hash_password  # noqa: E402
from app.shared.curriculum import Subject, Topic  # noqa: E402
from app.shared.identity import GuardianLink, RoleAssignment, User  # noqa: E402
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear  # noqa: E402
from app.shared.types import Role  # noqa: E402


DEMO_SCHOOL_NAME = "DEMO Škola KOMPAS (ilustračné dáta)"


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.execute(select(School).where(School.name == DEMO_SCHOOL_NAME)).scalars().first()
        if existing:
            print(f"DEMO dáta už existujú (school_id={existing.id}, is_demo={existing.is_demo}). Nič sa nemení.")
            return 0

        school_id = uuid.uuid4()
        year_id = uuid.uuid4()
        class_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        topic_id = uuid.uuid4()

        ids = {r: uuid.uuid4() for r in ["student", "teacher", "leadership", "parent"]}
        pw = hash_password("demo-password")

        db.add(School(id=school_id, name=DEMO_SCHOOL_NAME, is_demo=True))
        db.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27 (DEMO)", is_demo=True))
        db.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="DEMO-5A", grade=5, is_demo=True))

        users = [
            (ids["student"], "demo_student", "DEMO Žiak", Role.STUDENT),
            (ids["teacher"], "demo_teacher", "DEMO Učiteľ", Role.TEACHER),
            (ids["leadership"], "demo_leadership", "DEMO Vedenie", Role.LEADERSHIP),
            (ids["parent"], "demo_parent", "DEMO Rodič", Role.PARENT),
        ]
        for uid, uname, fname, role in users:
            db.add(User(id=uid, school_id=school_id, username=uname, full_name=fname, password_hash=pw, is_demo=True))
            db.add(RoleAssignment(user_id=uid, school_id=school_id, role=role.value, is_demo=True))

        db.add(Enrollment(id=uuid.uuid4(), school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=ids["student"], is_demo=True))
        db.add(GuardianLink(id=uuid.uuid4(), guardian_user_id=ids["parent"], child_user_id=ids["student"], school_id=school_id, relationship="demo", is_demo=True))

        db.add(Subject(id=subject_id, school_id=school_id, name="DEMO Matematika", is_demo=True))
        db.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name="DEMO Zlomky", grade=5, order_index=1, is_demo=True))

        ct = Base.metadata.tables.get("school_class_teacher")
        if ct is not None:
            db.execute(insert(ct).values(
                id=uuid.uuid4(), school_id=school_id, class_group_id=class_id, teacher_user_id=ids["teacher"],
                valid_from=datetime.now(timezone.utc), valid_to=None, version=1, is_demo=True,
            ))

        db.commit()
        print("DEMO dáta vytvorené (ilustračné, is_demo=true).")
        print(f"school_id={school_id} school_year_id={year_id} class_id={class_id} topic_id={topic_id}")
        print("Používatelia (heslo: demo-password):")
        for _, uname, fname, role in users:
            print(f"  - {role.value}: {uname} ({fname})")
        print("UPOZORNENIE: Tieto údaje sú iba demonštračné a nepredstavujú skutočné osoby.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
