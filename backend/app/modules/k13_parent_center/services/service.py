from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k13_parent_center.repository.repository import K13Repository
from app.shared.types import Principal, Role


class K13Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K13Repository(db)

    def _authorize_guardian(self, principal: Principal, action: str, resource: str, *, child_user_id: uuid.UUID, school_id: uuid.UUID):
        if principal.is_system:
            return
        ctx = {
            "scope": Scope.GUARDIAN_OF.value,
            "student_user_id": child_user_id,
            "child_user_id": child_user_id,
            "school_id": school_id,
        }
        decision = authorize(principal, action, resource, context=ctx, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def list_children(self, principal: Principal, *, school_id: uuid.UUID):
        action = "k13.list_children"
        resource = f"parent:{principal.user_id}:children"
        if not (principal.is_system or principal.role == Role.PARENT):
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": "not_parent"})
            raise PermissionError("not_parent")
        children = self.repo.list_linked_children(principal.user_id, school_id=school_id) if not principal.is_system else []
        audit_write(self.db, principal, action, resource, None, "success", {"count": len(children)})
        return {"child_user_ids": [str(c) for c in children]}

    def get_child_overview(self, principal: Principal, *, school_id: uuid.UUID, child_user_id: uuid.UUID):
        action = "k13.get_child_overview"
        resource = f"student:{child_user_id}:parent_overview"
        self._authorize_guardian(principal, action, resource, child_user_id=child_user_id, school_id=school_id)
        progress = self.repo.get_child_progress_summary(school_id, child_user_id)
        # approved information only; teacher private notes are excluded
        notes = self.repo.get_visible_teacher_notes(school_id, child_user_id)
        payload = {
            "child_user_id": str(child_user_id),
            "child_full_name": self.repo.get_user_full_name(child_user_id),
            "progress": progress,
            "teacher_notes": notes,
        }
        audit_write(self.db, principal, action, resource, None, "success")
        return payload
