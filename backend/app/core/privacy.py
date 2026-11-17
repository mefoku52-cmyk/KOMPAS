from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.api import serialize
from app.core.audit.logger import write as audit_write
from app.core.database.session import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.core.security.auth import get_current_principal
from app.modules.k01_learning_profile.domain.models import StudentLearningProfile
from app.modules.k04_missions.domain.models import MissionAttempt
from app.modules.k05_knowledge_continuity.domain.models import TopicState
from app.shared.identity import GuardianLink, RoleAssignment, User
from app.shared.school import ClassGroup, Enrollment, SchoolYear
from app.shared.types import Principal, Role, new_uuid, utc_now

router = APIRouter(prefix="/privacy", tags=["privacy"])


def _load_student(db: Session, student_user_id: uuid.UUID) -> User:
    student = db.get(User, student_user_id)
    if student is None:
        raise NotFoundError("student_not_found")
    role = db.execute(
        select(RoleAssignment.role).where(RoleAssignment.user_id == student_user_id, RoleAssignment.role == Role.STUDENT.value)
    ).first()
    if role is None:
        raise NotFoundError("student_not_found")
    return student


def _authorize(db: Session, principal: Principal, student: User) -> None:
    if principal.role == Role.STUDENT and principal.user_id == student.id:
        return
    if principal.role == Role.LEADERSHIP and principal.school_id == student.school_id:
        return
    if principal.role == Role.PARENT:
        link = db.execute(
            select(GuardianLink.id).where(
                GuardianLink.guardian_user_id == principal.user_id,
                GuardianLink.child_user_id == student.id,
                GuardianLink.school_id == student.school_id,
            )
        ).first()
        if link is not None:
            return
    raise ForbiddenError("export_forbidden")


def export_student_data(db: Session, principal: Principal, student_user_id: uuid.UUID, purpose: str) -> dict[str, Any]:
    student = _load_student(db, student_user_id)
    _authorize(db, principal, student)

    roles = db.execute(select(RoleAssignment).where(RoleAssignment.user_id == student.id)).scalars().all()
    enrollment_rows = db.execute(
        select(Enrollment, SchoolYear, ClassGroup)
        .join(SchoolYear, SchoolYear.id == Enrollment.school_year_id)
        .join(ClassGroup, ClassGroup.id == Enrollment.class_group_id)
        .where(Enrollment.student_user_id == student.id)
        .order_by(SchoolYear.name.asc(), ClassGroup.name.asc())
    ).all()
    profiles = db.execute(
        select(StudentLearningProfile).where(StudentLearningProfile.student_user_id == student.id)
        .order_by(StudentLearningProfile.valid_from.asc())
    ).scalars().all()
    knowledge = db.execute(
        select(TopicState).where(TopicState.student_user_id == student.id)
        .order_by(TopicState.valid_from.asc())
    ).scalars().all()
    attempts = db.execute(
        select(MissionAttempt).where(MissionAttempt.student_user_id == student.id)
        .order_by(MissionAttempt.valid_from.asc())
    ).scalars().all()

    payload = {
        "export_id": str(new_uuid()),
        "exported_at": utc_now().isoformat(),
        "purpose": purpose,
        "identity": {
            "id": str(student.id),
            "school_id": str(student.school_id),
            "username": student.username,
            "full_name": student.full_name,
            "is_active": student.is_active,
        },
        "roles": [serialize(row) for row in roles],
        "enrollments": [
            {
                "enrollment": serialize(enrollment),
                "school_year": serialize(year),
                "class_group": serialize(class_group),
            }
            for enrollment, year, class_group in enrollment_rows
        ],
        "learning_profiles": [serialize(row) for row in profiles],
        "knowledge_states": [serialize(row) for row in knowledge],
        "mission_attempts": [serialize(row) for row in attempts],
    }
    audit_write(
        db, principal, "privacy.export_student_data", f"identity_user:{student.id}", purpose, "success",
        {"sections": ["identity", "roles", "enrollments", "learning_profiles", "knowledge_states", "mission_attempts"]},
    )
    db.commit()
    return payload


@router.get("/students/{student_user_id}/export")
def student_export(
    student_user_id: uuid.UUID,
    purpose: str = Query(..., min_length=3, max_length=255),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return export_student_data(db, principal, student_user_id, purpose)
