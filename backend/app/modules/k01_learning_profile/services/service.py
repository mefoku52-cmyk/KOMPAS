from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k01_learning_profile.repository.repository import K01Repository
from app.shared.types import Principal, Role


class K01Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K01Repository(db)

    def _authorize_or_raise(self, principal: Principal, action: str, resource: str, context: dict, purpose: str | None = None):
        decision = authorize(principal, action, resource, context=context, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, purpose, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        return decision

    def _view_context(
        self,
        principal: Principal,
        *,
        student_user_id: uuid.UUID,
        school_id: uuid.UUID,
        purpose: str | None = None,
        class_group_id: uuid.UUID | None = None,
        teacher_user_id: uuid.UUID | None = None,
        teaches: bool = False,
    ) -> dict:
        if principal.is_system:
            return {"school_id": school_id, "system_internal": True}
        if principal.user_id == student_user_id:
            return {"scope": Scope.SELF.value, "owner_user_id": student_user_id, "student_user_id": student_user_id, "school_id": school_id}
        if principal.role == Role.PARENT:
            return {"scope": Scope.GUARDIAN_OF.value, "student_user_id": student_user_id, "child_user_id": student_user_id, "school_id": school_id}
        if principal.role == Role.TEACHER:
            return {
                "scope": Scope.TEACHES_CLASS.value,
                "student_user_id": student_user_id,
                "class_group_id": class_group_id,
                "teacher_user_id": principal.user_id if teaches else teacher_user_id,
                "teaches": teaches,
                "school_id": school_id,
            }
        if principal.role == Role.LEADERSHIP:
            return {
                "scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value,
                "school_id": school_id,
                "student_user_id": student_user_id,
                "purpose": purpose,
            }
        return {"school_id": school_id}

    def create_profile(
        self,
        principal: Principal,
        *,
        school_id: uuid.UUID,
        student_user_id: uuid.UUID,
        school_year_id: uuid.UUID,
        grade: int,
        label: str | None = None,
        version: int = 1,
        is_demo: bool = False,
        purpose: str | None = None,
        class_group_id: uuid.UUID | None = None,
        teaches: bool = False,
    ):
        action = "k01.create_profile"
        resource = f"progress_student_profile:student:{student_user_id}"
        if principal.is_system:
            ctx = {"school_id": school_id, "system_internal": True}
        elif principal.role == Role.TEACHER:
            ctx = {
                "scope": Scope.TEACHES_CLASS.value,
                "student_user_id": student_user_id,
                "class_group_id": class_group_id,
                "teacher_user_id": principal.user_id if teaches else None,
                "teaches": teaches,
                "school_id": school_id,
            }
        elif principal.role == Role.LEADERSHIP:
            ctx = {
                "scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value,
                "school_id": school_id,
                "student_user_id": student_user_id,
                "purpose": purpose,
            }
        else:
            ctx = {"school_id": school_id}
        self._authorize_or_raise(principal, action, resource, ctx, purpose=purpose)
        obj = self.repo.create_profile(
            school_id=school_id,
            student_user_id=student_user_id,
            school_year_id=school_year_id,
            grade=grade,
            label=label,
            version=version,
            is_demo=is_demo,
        )
        audit_write(self.db, principal, action, resource, purpose, "success", {"profile_id": str(obj.id), "school_year_id": str(school_year_id), "version": version})
        return obj

    def list_history(
        self,
        principal: Principal,
        student_user_id: uuid.UUID,
        school_id: uuid.UUID,
        *,
        purpose: str | None = None,
        class_group_id: uuid.UUID | None = None,
        teaches: bool = False,
    ):
        action = "k01.list_history"
        resource = f"progress_student_profile:student:{student_user_id}"
        ctx = self._view_context(
            principal,
            student_user_id=student_user_id,
            school_id=school_id,
            purpose=purpose,
            class_group_id=class_group_id,
            teaches=teaches,
        )
        self._authorize_or_raise(principal, action, resource, ctx, purpose=purpose)
        rows = self.repo.list_history(student_user_id, school_id=school_id)
        audit_write(self.db, principal, action, resource, purpose, "success", {"count": len(rows)})
        return rows

    def get_latest_for_year(
        self,
        principal: Principal,
        student_user_id: uuid.UUID,
        school_year_id: uuid.UUID,
        school_id: uuid.UUID,
        *,
        purpose: str | None = None,
        class_group_id: uuid.UUID | None = None,
        teaches: bool = False,
    ):
        action = "k01.get_profile"
        resource = f"progress_student_profile:student:{student_user_id}"
        ctx = self._view_context(
            principal,
            student_user_id=student_user_id,
            school_id=school_id,
            purpose=purpose,
            class_group_id=class_group_id,
            teaches=teaches,
        )
        self._authorize_or_raise(principal, action, resource, ctx, purpose=purpose)
        row = self.repo.get_latest_for_year(student_user_id, school_year_id, school_id=school_id)
        audit_write(self.db, principal, action, resource, purpose, "success", {"found": bool(row)})
        return row
