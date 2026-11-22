"""K18 RBAC helpers - maps IL operations to core policy scopes."""
from __future__ import annotations

import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.database.session import Base
from app.core.permissions.policy import Scope, authorize
from app.shared.types import Principal, Role
from app.shared.school import Enrollment
from app.shared.identity import GuardianLink


def _audit(db: Session, principal: Principal, action: str, resource: str, outcome: str, detail: dict | None = None):
    try:
        audit_write(db, principal, action, resource, None, outcome, detail or {})
    except Exception:
        pass  # audit must not break read path; K18 IL audit also records


def require_role(principal: Principal | None, roles: set[Role]):
    if principal is None:
        raise HTTPException(401, "auth required")
    if principal.is_system:
        return
    if principal.role not in roles:
        raise HTTPException(403, "forbidden")


def _teacher_assigned(db: Session, school_id, class_group_id, teacher_user_id) -> bool:
    table = Base.metadata.tables.get("school_class_teacher")
    if table is None or not class_group_id:
        return False
    stmt = select(table.c.id).where(
        table.c.school_id == school_id,
        table.c.class_group_id == class_group_id,
        table.c.teacher_user_id == teacher_user_id,
    )
    return db.execute(stmt).first() is not None


def can_access_student(db: Session, principal: Principal, student_user_id: str | uuid.UUID) -> bool:
    if principal.is_system:
        return True
    try:
        sid = uuid.UUID(str(student_user_id))
    except Exception:
        return False
    if principal.role == Role.STUDENT:
        return principal.user_id == sid
    if principal.role == Role.PARENT:
        ctx = {"scope": Scope.GUARDIAN_OF.value, "student_user_id": sid, "child_user_id": sid, "school_id": principal.school_id}
        return authorize(principal, "k18.read", f"student:{sid}", context=ctx, db=db).allowed
    if principal.role == Role.TEACHER:
        # allowed if teacher teaches any class where student is enrolled
        q = select(Enrollment.class_group_id).where(Enrollment.student_user_id == sid)
        if principal.school_id:
            q = q.where(Enrollment.school_id == principal.school_id)
        class_ids = [r[0] for r in db.execute(q).all()]
        for cid in class_ids:
            if _teacher_assigned(db, principal.school_id, cid, principal.user_id):
                ctx = {"scope": Scope.TEACHES_CLASS.value, "student_user_id": sid, "class_group_id": cid, "teacher_user_id": principal.user_id, "teaches": True, "school_id": principal.school_id}
                if authorize(principal, "k18.read", f"student:{sid}", context=ctx, db=db).allowed:
                    return True
        return False
    if principal.role == Role.LEADERSHIP:
        ctx = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": principal.school_id}
        return authorize(principal, "k18.read", f"student:{sid}", context=ctx, db=db).allowed
    return False


def require_student_access(db: Session, principal: Principal, student_user_id: str | uuid.UUID, action: str = "k18.read"):
    if not can_access_student(db, principal, student_user_id):
        _audit(db, principal, action, f"student:{student_user_id}", "denied", {"reason": "scope_denied"})
        raise HTTPException(403, "forbidden")


def require_leadership(db: Session, principal: Principal, action: str = "k18.admin"):
    if principal is None:
        raise HTTPException(401, "auth required")
    if principal.is_system:
        return
    ctx = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": principal.school_id}
    if principal.role != Role.LEADERSHIP or not authorize(principal, action, "intelligence", context=ctx, db=db).allowed:
        _audit(db, principal, action, "intelligence", "denied", {"reason": "leadership_required"})
        raise HTTPException(403, "forbidden")


def filter_initiatives_for_principal(db: Session, principal: Principal, initiatives):
    if principal.is_system or principal.role == Role.LEADERSHIP:
        return initiatives
    if principal.role in (Role.STUDENT, Role.PARENT):
        out = []
        for i in initiatives:
            if i.entity_type == "student" and can_access_student(db, principal, i.entity_id):
                out.append(i)
        return out
    if principal.role == Role.TEACHER:
        out = []
        for i in initiatives:
            if i.entity_type == "student" and can_access_student(db, principal, i.entity_id):
                out.append(i)
            elif i.entity_type != "student":
                # class/group signals: only leadership/teacher? allow teacher for now if same school
                if principal.school_id and (i.school_id is None or i.school_id == principal.school_id):
                    out.append(i)
        return out
    return []
