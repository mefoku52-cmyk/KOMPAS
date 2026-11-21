from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.database.session import Base
from app.core.permissions.policy import Scope, authorize
from app.modules.k09_class_overview.repository.repository import K09Repository
from app.shared.types import Principal, Role


class K09Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K09Repository(db)

    def _teacher_assigned(self, school_id: uuid.UUID, class_group_id: uuid.UUID, teacher_user_id: uuid.UUID) -> bool:
        table = Base.metadata.tables.get("school_class_teacher")
        if table is None:
            return False
        stmt = select(table.c.id).where(
            table.c.school_id == school_id,
            table.c.class_group_id == class_group_id,
            table.c.teacher_user_id == teacher_user_id,
        )
        return self.db.execute(stmt).first() is not None

    def _authorize_class_access(self, principal: Principal, school_id: uuid.UUID, class_group_id: uuid.UUID, action: str):
        resource = f"school_class_group:{class_group_id}"
        if principal.is_system:
            return {"school_id": school_id, "system_internal": True}
        if principal.role == Role.TEACHER:
            assigned = self._teacher_assigned(school_id, class_group_id, principal.user_id)
            students = self.repo.list_student_ids_in_class(school_id, class_group_id)
            if assigned and students:
                ctx = {
                    "scope": Scope.TEACHES_CLASS.value,
                    "student_user_id": students[0],
                    "class_group_id": class_group_id,
                    "teacher_user_id": principal.user_id,
                    "teaches": True,
                    "school_id": school_id,
                }
            elif assigned and not students:
                # no enrolled students, still allow teacher of class via aggregate-like internal grant not modeled; deny by policy -> explicit allow path
                ctx = {"school_id": school_id, "system_internal": False}
                audit_write(self.db, principal, action, resource, None, "denied", {"reason": "no_students"})
                raise PermissionError("no_students")
            else:
                ctx = {"school_id": school_id}
            decision = authorize(principal, action, resource, context=ctx, db=self.db)
            if not decision.allowed:
                audit_write(self.db, principal, action, resource, None, "denied", {"reason": decision.reason})
                raise PermissionError(decision.reason)
            return ctx
        ctx = {"school_id": school_id}
        decision = authorize(principal, action, resource, context=ctx, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        return ctx

    def list_my_classes(self, principal: Principal, *, school_id: uuid.UUID) -> list[dict]:
        action = "k09.list_classes"
        if not principal.is_system and principal.role != Role.TEACHER:
            audit_write(self.db, principal, action, "school_class_group:list", None, "denied", {"reason": "teacher_only"})
            raise PermissionError("teacher_only")
        classes = self.repo.list_classes_for_teacher(school_id, principal.user_id)
        audit_write(self.db, principal, action, "school_class_group:list", None, "success", {"count": len(classes)})
        return classes

    def get_class_overview(self, principal: Principal, *, school_id: uuid.UUID, class_group_id: uuid.UUID, topic_id: uuid.UUID | None = None):
        action = "k09.get_class_overview"
        resource = f"school_class_group:{class_group_id}"
        self._authorize_class_access(principal, school_id, class_group_id, action)
        students = self.repo.list_student_ids_in_class(school_id, class_group_id)
        dist = self.repo.get_topic_state_distribution(school_id, students, topic_id=topic_id)
        audit_write(self.db, principal, action, resource, None, "success", {"student_count": len(students)})
        return {"class_group_id": str(class_group_id), **dist}
