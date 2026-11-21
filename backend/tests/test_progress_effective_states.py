"""Effective state rule: practice never downgrades, verification always applies."""

from __future__ import annotations

import uuid
from collections import namedtuple
from datetime import datetime, timedelta, timezone

from app.core.database.session import Base
from app.modules.k03_adaptive_learning.services.service import K03Service
from app.modules.k05_knowledge_continuity.services.service import K05Service
from app.modules.k09_class_overview.repository.repository import K09Repository
from app.modules.k13_parent_center.repository.repository import K13Repository
from app.shared.curriculum import Subject, Topic
from app.shared.identity import User
from app.shared.progress import resolve_effective_states
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.shared.types import Principal, Role, system_principal

Row = namedtuple("Row", "topic_id kind status valid_from version")

T0 = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)


def _row(kind: str, status: str, minutes: int, version: int = 1, topic_id=None):
    return Row(
        topic_id=topic_id or uuid.UUID(int=1),
        kind=kind,
        status=status,
        valid_from=T0 + timedelta(minutes=minutes),
        version=version,
    )


def _status(rows):
    states = resolve_effective_states(rows, key=lambda r: r.topic_id)
    return next(iter(states.values())).status


def test_practice_cannot_downgrade_verified():
    rows = [
        _row("verified", "verified_mastery", 1),
        _row("practiced", "in_progress_practice", 2),
    ]
    assert _status(rows) == "verified_mastery"


def test_practice_cannot_downgrade_partially_mastered():
    rows = [
        _row("practiced", "partially_mastered", 1),
        _row("practiced", "in_progress_practice", 2),
    ]
    assert _status(rows) == "partially_mastered"


def test_practice_can_lift_status():
    rows = [
        _row("practiced", "in_progress_practice", 1),
        _row("practiced", "partially_mastered", 2),
    ]
    assert _status(rows) == "partially_mastered"


def test_failed_verification_downgrades():
    rows = [
        _row("verified", "verified_mastery", 1),
        _row("verified", "partially_mastered", 2),
    ]
    assert _status(rows) == "partially_mastered"


def test_unordered_rows_are_folded_chronologically():
    rows = [
        _row("practiced", "in_progress_practice", 3),
        _row("verified", "verified_mastery", 1),
        _row("practiced", "partially_mastered", 2),
    ]
    assert _status(rows) == "verified_mastery"


def test_same_timestamp_uses_version_order():
    rows = [
        _row("verified", "verified_mastery", 1, version=2),
        _row("verified", "partially_mastered", 1, version=1),
    ]
    assert _status(rows) == "verified_mastery"


# --- integration: every reader agrees on the effective state -----------------

def _seed(db):
    school_id, year_id, class_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    subject_id, topic_id, student_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    db.add(School(id=school_id, name="EffectiveStateSchool", is_demo=True))
    db.flush()
    db.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27", is_demo=True))
    db.add(ClassGroup(id=class_id, school_id=school_id, school_year_id=year_id, name="5A", grade=5, is_demo=True))
    db.add(Subject(id=subject_id, school_id=school_id, name="Matematika", is_demo=True))
    db.add(Topic(id=topic_id, school_id=school_id, subject_id=subject_id, name="Zlomky", grade=5, order_index=1, is_demo=True))
    db.add(User(id=student_id, school_id=school_id, username="eff-student", full_name="Demo Student", password_hash="x", is_demo=True))
    db.add(Enrollment(id=uuid.uuid4(), school_id=school_id, school_year_id=year_id, class_group_id=class_id, student_user_id=student_id, is_demo=True))
    db.commit()
    return school_id, class_id, topic_id, student_id


def test_all_readers_keep_verified_mastery_after_wrong_practice(db_session):
    school_id, class_id, topic_id, student_id = _seed(db_session)
    svc = K05Service(db_session)
    sys_p = system_principal()
    common = dict(school_id=school_id, student_user_id=student_id, topic_id=topic_id, is_demo=True)
    svc.record_state(
        sys_p, kind="verified", status="verified_mastery",
        evidence_attempt_ref="v1", is_verification_evidence=True, **common,
    )
    svc.record_state(sys_p, kind="practiced", status="in_progress_practice", evidence_attempt_ref="p2", **common)
    db_session.commit()

    student = Principal(user_id=student_id, role=Role.STUDENT, school_id=school_id, scopes=())

    recs = K03Service(db_session).recommend_for_student(student, school_id=school_id, student_user_id=student_id)
    assert recs == []

    k09 = K09Repository(db_session).get_topic_state_distribution(
        school_id=school_id, student_user_ids=[student_id]
    )
    assert k09["by_status"] == {"verified_mastery": 1}

    k13 = K13Repository(db_session).get_child_progress_summary(school_id, student_id)
    assert k13["by_status"] == {"verified_mastery": 1}

    # a failed verification legitimately downgrades
    svc.record_state(
        sys_p, kind="verified", status="partially_mastered",
        evidence_attempt_ref="v3", is_verification_evidence=True, **common,
    )
    db_session.commit()
    k13 = K13Repository(db_session).get_child_progress_summary(school_id, student_id)
    assert k13["by_status"] == {"partially_mastered": 1}
