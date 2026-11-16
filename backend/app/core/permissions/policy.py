from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.identity import GuardianLink, RoleAssignment
from app.shared.school import ClassGroup, Enrollment
from app.shared.types import Principal, Role


class Scope(str, enum.Enum):
    SELF = "SELF"
    GUARDIAN_OF = "GUARDIAN_OF"
    TEACHES_CLASS = "TEACHES_CLASS"
    SCHOOL_AGGREGATE = "SCHOOL_AGGREGATE"
    SCHOOL_INDIVIDUAL_WITH_PURPOSE = "SCHOOL_INDIVIDUAL_WITH_PURPOSE"


class Visibility(str, enum.Enum):
    TEACHER_PRIVATE_NOTE = "TEACHER_PRIVATE_NOTE"
    PARENT_PRIVATE_COMMUNICATION = "PARENT_PRIVATE_COMMUNICATION"


@dataclass
class Decision:
    allowed: bool
    reason: str


def _deny(reason: str) -> Decision:
    return Decision(False, reason)


def _allow(reason: str) -> Decision:
    return Decision(True, reason)


def _has_role(db: Session, principal: Principal, role: Role) -> bool:
    stmt = select(RoleAssignment).where(
        RoleAssignment.user_id == principal.user_id,
        RoleAssignment.role == role.value,
    )
    if principal.school_id:
        stmt = stmt.where(RoleAssignment.school_id == principal.school_id)
    return db.execute(stmt).scalar_one_or_none() is not None


def _is_guardian_of(db: Session, principal: Principal, child_user_id: Any) -> bool:
    stmt = select(GuardianLink).where(
        GuardianLink.guardian_user_id == principal.user_id,
        GuardianLink.child_user_id == child_user_id,
    )
    if principal.school_id:
        stmt = stmt.where(GuardianLink.school_id == principal.school_id)
    return db.execute(stmt).scalar_one_or_none() is not None


def _teaches_class_of(db: Session, principal: Principal, student_user_id: Any) -> bool:
    # teacher teaches class: teacher assigned to class_group via teacher_user_id if present, else via role+enrollment same class
    # minimal: enrollment in a class where principal is teacher of that class (class has teacher_user_id attr optional not modeled; fallback: TEACHES_CLASS scope context provides class_id and we verify enrollment)
    class_id = None
    # context handled outside; here check enrollment exists for same school
    stmt = select(Enrollment).where(Enrollment.student_user_id == student_user_id)
    if principal.school_id:
        stmt = stmt.where(Enrollment.school_id == principal.school_id)
    enrollments = db.execute(stmt).scalars().all()
    if not enrollments:
        return False
    # if teacher, require context-provided class_id match
    # fallback allow if same school and principal states TEACHES_CLASS with matching class in context (validated in authorize)
    return True


def authorize(principal: Optional[Principal], action: str, resource: str, context: Optional[dict[str, Any]] = None, db: Optional[Session] = None) -> Decision:
    ctx = context or {}
    if principal is None:
        return _deny("no_principal")

    visibility = ctx.get("visibility")
    if visibility == Visibility.TEACHER_PRIVATE_NOTE.value or visibility == Visibility.TEACHER_PRIVATE_NOTE:
        if principal.role == Role.TEACHER and ctx.get("owner_user_id") == principal.user_id:
            return _allow("teacher_private_owner")
        return _deny("teacher_private_note_restricted")
    if visibility == Visibility.PARENT_PRIVATE_COMMUNICATION.value or visibility == Visibility.PARENT_PRIVATE_COMMUNICATION:
        participants = ctx.get("participants") or []
        if principal.user_id in participants:
            return _allow("parent_private_participant")
        return _deny("parent_private_communication_restricted")

    scope = ctx.get("scope")

    if scope == Scope.SELF.value or scope == Scope.SELF:
        if ctx.get("owner_user_id") == principal.user_id or ctx.get("student_user_id") == principal.user_id:
            return _allow("self")
        return _deny("not_self")

    if scope == Scope.GUARDIAN_OF.value or scope == Scope.GUARDIAN_OF:
        if principal.role != Role.PARENT:
            return _deny("not_parent")
        child_id = ctx.get("student_user_id") or ctx.get("child_user_id")
        if child_id and db and _is_guardian_of(db, principal, child_id):
            return _allow("guardian_of")
        if child_id and not db:
            return _deny("db_required_for_guardian_check")
        return _deny("not_guardian_of")

    if scope == Scope.TEACHES_CLASS.value or scope == Scope.TEACHES_CLASS:
        if principal.role != Role.TEACHER:
            return _deny("not_teacher")
        class_id = ctx.get("class_group_id")
        student_id = ctx.get("student_user_id")
        if class_id and student_id and db:
            enrolled = db.execute(
                select(Enrollment).where(
                    Enrollment.class_group_id == class_id,
                    Enrollment.student_user_id == student_id,
                )
            ).scalar_one_or_none()
            teacher_of = ctx.get("teacher_user_id") == principal.user_id or ctx.get("teaches", False)
            if enrolled and teacher_of:
                return _allow("teaches_class")
            if enrolled and not teacher_of:
                return _deny("teacher_not_assigned_to_class")
        if not class_id or not student_id:
            return _deny("missing_class_or_student")
        return _deny("teaches_class_denied")

    if scope == Scope.SCHOOL_AGGREGATE.value or scope == Scope.SCHOOL_AGGREGATE:
        if principal.role == Role.LEADERSHIP and ctx.get("school_id") == principal.school_id:
            return _allow("school_aggregate")
        return _deny("school_aggregate_denied")

    if scope == Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value or scope == Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE:
        if principal.role == Role.LEADERSHIP and ctx.get("school_id") == principal.school_id:
            purpose = ctx.get("purpose")
            if purpose and str(purpose).strip():
                return _allow("school_individual_with_purpose")
            return _deny("purpose_required")
        return _deny("school_individual_denied")

    # system principal allowed for internal handlers when explicitly marked
    if principal.is_system and ctx.get("system_internal"):
        return _allow("system_internal")

    return _deny("deny_by_default")
