#!/usr/bin/env python3
"""
Demonštračné dáta pre KOMPAS (ilustračné, nie skutočné osobné údaje).
Všetky záznamy sú označené is_demo = true.

Spustenie (z koreňa repozitára):
  set -a; . ./.env; set +a
  PYTHONPATH=backend backend/.venv/bin/python scripts/seed_demo.py

Skript je idempotentný: základnú štruktúru (škola, používatelia, trieda) vytvorí raz,
obsahovú vrstvu (témy, stavy učiva, misie, knižnicu, plány, požiadavky, projekt,
komunikáciu) doplní, ak ešte neexistuje.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
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
import app.modules.k13_parent_center.domain.models  # noqa: F401,E402
import app.modules.k14_communication_center.domain.models  # noqa: F401,E402
import app.modules.k15_collaboration_projects.domain.models  # noqa: F401,E402
import app.modules.k16_intelligent_core.domain.models  # noqa: F401,E402

from app.core.security.auth import hash_password  # noqa: E402
from app.modules.k01_learning_profile.domain.models import StudentLearningProfile  # noqa: E402
from app.modules.k02_subject_workspace.domain.models import SubjectWorkspace, WorkspaceTopicNode  # noqa: E402
from app.modules.k04_missions.domain.models import Mission, MissionAttempt, MissionTask, TaskType  # noqa: E402
from app.modules.k05_knowledge_continuity.domain.models import (  # noqa: E402
    TopicProgressKind,
    TopicProgressStatus,
    TopicState,
)
from app.modules.k07_professional_library.domain.models import LibraryItem, LibraryTag, LibraryVersion  # noqa: E402
from app.modules.k08_work_assistant.domain.models import DraftStatus, WorkAssistantDraft  # noqa: E402
from app.modules.k10_organization_center.domain.models import OrgAssignment, OrgPlan, OrgTask  # noqa: E402
from app.modules.k11_operations_center.domain.models import OperationRequest, OperationRequestStatus  # noqa: E402
from app.modules.k14_communication_center.domain.models import (  # noqa: E402
    CommunicationMessage,
    CommunicationParticipant,
    CommunicationThread,
)
from app.modules.k15_collaboration_projects.domain.models import (  # noqa: E402
    CollaborationProject,
    ProjectMember,
    ProjectTask,
)
from app.shared.curriculum import Subject, Topic  # noqa: E402
from app.shared.identity import GuardianLink, RoleAssignment, User  # noqa: E402
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear  # noqa: E402
from app.shared.types import Role  # noqa: E402


DEMO_SCHOOL_NAME = "DEMO Škola KOMPAS (ilustračné dáta)"
DEMO_PASSWORD = "demo-password"

EXTRA_STUDENTS = [
    ("demo_student02", "DEMO Žiak 2"),
    ("demo_student03", "DEMO Žiak 3"),
    ("demo_student04", "DEMO Žiak 4"),
    ("demo_student05", "DEMO Žiak 5"),
    ("demo_student06", "DEMO Žiak 6"),
]

# (názov témy, poradie) - poradie 1 je pôvodná DEMO téma
TOPICS = [
    ("DEMO Zlomky", 1),
    ("DEMO Desatinné čísla", 2),
    ("DEMO Geometria – obvod a obsah", 3),
]

# stav učiva pre 6 žiakov x 3 témy (kind, status)
STUDENT_STATES = [
    # demo_student
    [("practiced", "in_progress_practice"), ("practiced", "partially_mastered"), ("verified", "verified_mastery")],
    # demo_student02
    [("verified", "verified_mastery"), ("verified", "verified_mastery"), ("practiced", "partially_mastered")],
    # demo_student03
    [("practiced", "in_progress_practice"), ("verified", "verified_mastery"), ("practiced", "in_progress_practice")],
    # demo_student04
    [("verified", "verified_mastery"), ("practiced", "partially_mastered"), ("verified", "verified_mastery")],
    # demo_student05
    [("practiced", "in_progress_practice"), ("practiced", "in_progress_practice"), ("verified", "verified_mastery")],
    # demo_student06
    [("practiced", "partially_mastered"), ("practiced", "partially_mastered"), ("practiced", "in_progress_practice")],
]

MISSIONS = [
    {
        "title": "Zlomky – precvičovanie",
        "topic_index": 0,
        "is_verification": False,
        "tasks": [
            (TaskType.CHOICE.value, "1/2 + 1/4 = ?  (A) 2/6  (B) 3/4  (C) 1/6  — napíš písmeno správnej odpovede.", "B"),
            (TaskType.NUMERIC.value, "Koľko je 3/4 z 20? (napíš číslo)", "15"),
        ],
    },
    {
        "title": "Zlomky – overenie zvládnutia",
        "topic_index": 0,
        "is_verification": True,
        "tasks": [
            (TaskType.TEXT_MATCH.value, "Napíš zlomok ekvivalentný s 2/4 v tvare a/b.", "1/2"),
            (TaskType.NUMERIC.value, "5/6 - 1/3 = ? (výsledok zapíš ako desatinné číslo)", "0.5"),
        ],
    },
    {
        "title": "Desatinné čísla – precvičovanie",
        "topic_index": 1,
        "is_verification": False,
        "tasks": [
            (TaskType.NUMERIC.value, "0,5 + 0,25 = ?", "0.75"),
            (TaskType.CHOICE.value, "Ktoré číslo je najväčšie?  (A) 0,7  (B) 0,07  (C) 0,17 — napíš písmeno.", "A"),
        ],
    },
]


def _school_context(db):
    school = db.execute(select(School).where(School.name == DEMO_SCHOOL_NAME)).scalars().first()
    if school is None:
        return None
    year = db.execute(select(SchoolYear).where(SchoolYear.school_id == school.id)).scalars().first()
    klass = db.execute(select(ClassGroup).where(ClassGroup.school_id == school.id)).scalars().first()
    subject = db.execute(select(Subject).where(Subject.school_id == school.id)).scalars().first()
    return school, year, klass, subject


def _existing_usernames(db) -> dict[str, uuid.UUID]:
    rows = db.execute(select(User.username, User.id)).all()
    return {username: user_id for username, user_id in rows}


def _content_seeded(db, school_id: uuid.UUID) -> bool:
    return db.execute(select(Mission.id).where(Mission.school_id == school_id)).first() is not None


def create_base(db) -> int:
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    topic_id = uuid.uuid4()

    ids = {r: uuid.uuid4() for r in ["student", "teacher", "leadership", "parent"]}
    pw = hash_password(DEMO_PASSWORD)

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
    db.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name=TOPICS[0][0], grade=5, order_index=TOPICS[0][1], is_demo=True))

    ct = Base.metadata.tables.get("school_class_teacher")
    if ct is not None:
        db.execute(insert(ct).values(
            id=uuid.uuid4(), school_id=school_id, class_group_id=class_id, teacher_user_id=ids["teacher"],
            valid_from=datetime.now(timezone.utc), valid_to=None, version=1, is_demo=True,
        ))

    db.commit()
    print("Základné DEMO dáta vytvorené (ilustračné, is_demo=true).")
    print("Používatelia (heslo: demo-password):")
    for _, uname, fname, role in users:
        print(f"  - {role.value}: {uname} ({fname})")
    return 0


def create_content(db) -> int:
    ctx = _school_context(db)
    if ctx is None:
        print("Základné DEMO dáta chýbajú.")
        return 1
    school, year, klass, subject = ctx
    if year is None or klass is None or subject is None:
        print("Základné DEMO dáta sú neúplné (chýba školský rok / trieda / predmet).")
        return 1

    usernames = _existing_usernames(db)
    student_id = usernames.get("demo_student")
    teacher_id = usernames.get("demo_teacher")
    leadership_id = usernames.get("demo_leadership")
    parent_id = usernames.get("demo_parent")
    if not all([student_id, teacher_id, leadership_id, parent_id]):
        print("Základní DEMO používatelia chýbajú.")
        return 1

    # --- ďalší žiaci v triede (aby mali agregáty čo zobrazovať) ---
    pw = hash_password(DEMO_PASSWORD)
    student_ids = [student_id]
    for uname, fname in EXTRA_STUDENTS:
        existing_id = usernames.get(uname)
        if existing_id is None:
            existing_id = uuid.uuid4()
            db.add(User(id=existing_id, school_id=school.id, username=uname, full_name=fname, password_hash=pw, is_demo=True))
            db.add(RoleAssignment(user_id=existing_id, school_id=school.id, role=Role.STUDENT.value, is_demo=True))
            db.add(Enrollment(id=uuid.uuid4(), school_id=school.id, school_year_id=year.id, class_group_id=klass.id, student_user_id=existing_id, is_demo=True))
        student_ids.append(existing_id)
    db.flush()

    # --- témy ---
    topics: list[Topic] = []
    for name, order_index in TOPICS:
        topic = db.execute(
            select(Topic).where(Topic.school_id == school.id, Topic.name == name)
        ).scalars().first()
        if topic is None:
            topic = Topic(
                id=uuid.uuid4(), school_id=school.id, subject_id=subject.id,
                name=name, grade=5, order_index=order_index, is_demo=True,
            )
            db.add(topic)
            db.flush()
        topics.append(topic)

    # --- K01 profil každého žiaka ---
    for sid in student_ids:
        profile = db.execute(
            select(StudentLearningProfile).where(
                StudentLearningProfile.school_id == school.id,
                StudentLearningProfile.student_user_id == sid,
                StudentLearningProfile.school_year_id == year.id,
            )
        ).scalars().first()
        if profile is None:
            db.add(StudentLearningProfile(
                id=uuid.uuid4(), school_id=school.id, student_user_id=sid,
                school_year_id=year.id, grade=5, label="DEMO profil", version=1, is_demo=True,
            ))

    # --- K05 stavy učiva ---
    for sid, states in zip(student_ids, STUDENT_STATES):
        for topic, (kind, status) in zip(topics, states):
            existing = db.execute(
                select(TopicState.id).where(
                    TopicState.school_id == school.id,
                    TopicState.student_user_id == sid,
                    TopicState.topic_id == topic.id,
                )
            ).first()
            if existing:
                continue
            db.add(TopicState(
                id=uuid.uuid4(), school_id=school.id, student_user_id=sid, topic_id=topic.id,
                kind=TopicProgressKind(kind), status=TopicProgressStatus(status),
                evidence_attempt_ref="demo-seed", is_verification_evidence=(kind == "verified"),
                version=1, is_demo=True,
            ))

    # --- K02 pracovný priestor predmetu ---
    workspace = db.execute(
        select(SubjectWorkspace).where(
            SubjectWorkspace.school_id == school.id,
            SubjectWorkspace.subject_id == subject.id,
            SubjectWorkspace.teacher_user_id == teacher_id,
        )
    ).scalars().first()
    if workspace is None:
        workspace = SubjectWorkspace(
            id=uuid.uuid4(), school_id=school.id, subject_id=subject.id,
            teacher_user_id=teacher_id, name="DEMO Matematika – plán", is_demo=True,
        )
        db.add(workspace)
        db.flush()
        for index, topic in enumerate(topics):
            db.add(WorkspaceTopicNode(
                id=uuid.uuid4(), school_id=school.id, workspace_id=workspace.id,
                topic_id=topic.id, title=topic.name, order_index=index, is_demo=True,
            ))

    # --- K04 misie, úlohy a pokusy ---
    mission_ids: list[uuid.UUID] = []
    task_ids: list[uuid.UUID] = []
    for mission_def in MISSIONS:
        mission = Mission(
            id=uuid.uuid4(), school_id=school.id, topic_id=topics[mission_def["topic_index"]].id,
            title=mission_def["title"], is_verification=mission_def["is_verification"],
            version=1, is_demo=True,
        )
        db.add(mission)
        db.flush()
        mission_ids.append(mission.id)
        for order_index, (task_type, prompt, expected) in enumerate(mission_def["tasks"]):
            task = MissionTask(
                id=uuid.uuid4(), school_id=school.id, mission_id=mission.id, task_type=task_type,
                prompt=prompt, expected_answer=expected, order_index=order_index,
                version=1, is_demo=True,
            )
            db.add(task)
            db.flush()
            task_ids.append(task.id)

    # dva ukážkové pokusy demo_studenta (jeden správny, jeden nesprávny)
    demo_attempts = [
        (task_ids[0], "B", True),
        (task_ids[1], "12", False),
    ]
    for task_id, answer, is_correct in demo_attempts:
        exists = db.execute(
            select(MissionAttempt.id).where(
                MissionAttempt.task_id == task_id,
                MissionAttempt.student_user_id == student_id,
            )
        ).first()
        if not exists:
            db.add(MissionAttempt(
                id=uuid.uuid4(), school_id=school.id, task_id=task_id,
                student_user_id=student_id, answer=answer, is_correct=is_correct,
                evaluated=True, version=1, is_demo=True,
            ))

    # --- K07 knižnica učiteľa ---
    library_items = [
        ("Zlomky – pracovný list", "Pracovný list na precvičenie zlomkov (5. ročník).", ["zlomky", "5. ročník"]),
        ("Desatinné čísla – test", "Krátky test s 5 úlohami na desatinné čísla.", ["test", "desatinné čísla"]),
    ]
    for title, description, tags in library_items:
        item = db.execute(
            select(LibraryItem).where(
                LibraryItem.school_id == school.id,
                LibraryItem.owner_teacher_user_id == teacher_id,
                LibraryItem.title == title,
            )
        ).scalars().first()
        if item is None:
            item = LibraryItem(
                id=uuid.uuid4(), school_id=school.id, owner_teacher_user_id=teacher_id,
                title=title, description=description, archived=False, version=1, is_demo=True,
            )
            db.add(item)
            db.flush()
            db.add(LibraryVersion(
                id=uuid.uuid4(), school_id=school.id, item_id=item.id, version_number=1,
                content_text=f"DEMO obsah: {title}", note="Prvá verzia", version=1, is_demo=True,
            ))
            for tag in tags:
                db.add(LibraryTag(id=uuid.uuid4(), school_id=school.id, item_id=item.id, tag=tag, version=1, is_demo=True))

    # --- K08 koncept asistenta ---
    draft = db.execute(
        select(WorkAssistantDraft).where(
            WorkAssistantDraft.school_id == school.id,
            WorkAssistantDraft.teacher_user_id == teacher_id,
        )
    ).scalars().first()
    if draft is None:
        db.add(WorkAssistantDraft(
            id=uuid.uuid4(), school_id=school.id, teacher_user_id=teacher_id,
            title="Návrh pracovného listu: Zlomky", draft_type="worksheet",
            content="1) 1/2 + 1/4 = ?  2) 3/4 z 20 = ?", status=DraftStatus.DRAFT.value,
            version=1, is_demo=True,
        ))

    # --- K10 organizačný plán a úlohy ---
    plan = db.execute(
        select(OrgPlan).where(OrgPlan.school_id == school.id, OrgPlan.name == "DEMO Plán 1. polrok")
    ).scalars().first()
    if plan is None:
        plan = OrgPlan(
            id=uuid.uuid4(), school_id=school.id, name="DEMO Plán 1. polrok",
            description="Ilustračný organizačný plán školy.", version=1, is_demo=True,
        )
        db.add(plan)
        db.flush()

    org_tasks = [
        ("Príprava triednych schôdzok", "Naplánovať triedne schôdzky pre všetky triedy.", "open", "garant"),
        ("Revizia učebníc", "Skontrolovať stav učebníc v kabinetoch.", "in_progress", "riešiteľ"),
        ("Školský výlet 5.A", "Pripraviť podklady pre školský výlet.", "done", "garant"),
    ]
    for index, (title, description, status, role_in_task) in enumerate(org_tasks):
        task = db.execute(
            select(OrgTask).where(OrgTask.school_id == school.id, OrgTask.title == title)
        ).scalars().first()
        if task is None:
            task = OrgTask(
                id=uuid.uuid4(), school_id=school.id, title=title, description=description,
                status=status, due_at=datetime.now(timezone.utc) + timedelta(days=7 * (index + 1)),
                version=1, is_demo=True,
            )
            db.add(task)
            db.flush()
            db.add(OrgAssignment(
                id=uuid.uuid4(), school_id=school.id, task_id=task.id,
                assignee_user_id=teacher_id if index % 2 == 0 else leadership_id,
                role_in_task=role_in_task, version=1, is_demo=True,
            ))

    # --- K11 prevádzkové požiadavky ---
    requests = [
        ("room", "Rezervácia telocvične", "Telocvičňa na štvrtok 4. hodinu.", OperationRequestStatus.SUBMITTED.value),
        ("equipment", "Nový dataprojektor do 5.A", "Súčasný projektor bliká.", OperationRequestStatus.APPROVED.value),
    ]
    for request_type, title, description, status in requests:
        exists = db.execute(
            select(OperationRequest.id).where(
                OperationRequest.school_id == school.id,
                OperationRequest.title == title,
            )
        ).first()
        if not exists:
            db.add(OperationRequest(
                id=uuid.uuid4(), school_id=school.id, requester_user_id=teacher_id,
                request_type=request_type, title=title, description=description,
                status=status, version=1, is_demo=True,
            ))

    # --- K14 komunikácia ---
    thread = db.execute(
        select(CommunicationThread).where(
            CommunicationThread.school_id == school.id,
            CommunicationThread.subject == "DEMO: Triedna schôdzka 5.A",
        )
    ).scalars().first()
    if thread is None:
        thread = CommunicationThread(
            id=uuid.uuid4(), school_id=school.id, subject="DEMO: Triedna schôdzka 5.A",
            is_private=False, created_by_user_id=teacher_id, version=1, is_demo=True,
        )
        db.add(thread)
        db.flush()
        for participant in (teacher_id, student_id, parent_id):
            db.add(CommunicationParticipant(
                id=uuid.uuid4(), school_id=school.id, thread_id=thread.id,
                user_id=participant, version=1, is_demo=True,
            ))
        db.add(CommunicationMessage(
            id=uuid.uuid4(), school_id=school.id, thread_id=thread.id, sender_user_id=teacher_id,
            body="Dobrý deň, triedna schôdzka bude vo štvrtok o 17:00.", version=1, is_demo=True,
        ))
        db.add(CommunicationMessage(
            id=uuid.uuid4(), school_id=school.id, thread_id=thread.id, sender_user_id=parent_id,
            body="Ďakujem, prídem.", version=1, is_demo=True,
        ))

    # --- K15 tímový projekt ---
    project = db.execute(
        select(CollaborationProject).where(
            CollaborationProject.school_id == school.id,
            CollaborationProject.title == "DEMO: Matematický deň",
        )
    ).scalars().first()
    if project is None:
        project = CollaborationProject(
            id=uuid.uuid4(), school_id=school.id, title="DEMO: Matematický deň",
            description="Spoločný projekt triedy 5.A – stanovištia s úlohami.",
            status="active", owner_user_id=teacher_id, version=1, is_demo=True,
        )
        db.add(project)
        db.flush()
        for member_id, role in ((teacher_id, "owner"), (student_id, "member"), (leadership_id, "sponsor")):
            db.add(ProjectMember(
                id=uuid.uuid4(), school_id=school.id, project_id=project.id,
                user_id=member_id, role=role, version=1, is_demo=True,
            ))
        for index, (title, status, assignee) in enumerate([
            ("Pripraviť stanovištia", "open", student_id),
            ("Zabezpečiť odmeny", "open", leadership_id),
            ("Rozpis služieb", "done", teacher_id),
        ]):
            db.add(ProjectTask(
                id=uuid.uuid4(), school_id=school.id, project_id=project.id, title=title,
                description=None, status=status, assignee_user_id=assignee,
                version=1, is_demo=True,
            ))

    db.commit()
    print("Obsahové DEMO dáta doplnené (témy, stavy, misie, knižnica, plány, požiadavky, projekt, komunikácia).")
    return 0


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.execute(select(School).where(School.name == DEMO_SCHOOL_NAME)).scalars().first()
        if existing is None:
            create_base(db)
            existing = db.execute(select(School).where(School.name == DEMO_SCHOOL_NAME)).scalars().one()
        else:
            print(f"Základné DEMO dáta už existujú (school_id={existing.id}).")
        if _content_seeded(db, existing.id):
            print("Obsahové DEMO dáta už existujú. Nič sa nemení.")
            return 0
        return create_content(db)
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
