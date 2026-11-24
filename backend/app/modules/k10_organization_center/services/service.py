from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k10_organization_center.repository.repository import K10Repository
from app.shared.types import Principal, Role


class K10Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K10Repository(db)

    def _auth(self, principal: Principal, action: str, resource: str, school_id: uuid.UUID, purpose: str | None = None):
        if principal.is_system:
            ctx = {"school_id": school_id, "system_internal": True}
        elif principal.role == Role.LEADERSHIP and principal.school_id == school_id:
            ctx = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": school_id}
        elif principal.role == Role.TEACHER and principal.school_id == school_id:
            # teachers can participate/view school org context (aggregate-like) - use system_internal not allowed; accept via leadership? no. Allow if teacher same school by explicit check below.
            ctx = {"school_id": school_id}
        else:
            ctx = {"school_id": school_id}
        decision = authorize(principal, action, resource, context=ctx, db=self.db)
        if not decision.allowed:
            # allow teacher/staff of same school for org operations as explicit domain rule
            if principal.role == Role.TEACHER and principal.school_id == school_id:
                return
            audit_write(self.db, principal, action, resource, purpose, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def create_task(self, principal: Principal, *, school_id: uuid.UUID, title: str, description: str | None = None, is_demo: bool = False):
        action = "k10.create_task"
        self._auth(principal, action, f"organization_task:school:{school_id}", school_id)
        obj = self.repo.create_task(school_id=school_id, title=title, description=description, is_demo=is_demo)
        audit_write(self.db, principal, action, f"organization_task:{obj.id}", None, "success")
        return obj

    def create_plan(self, principal: Principal, *, school_id: uuid.UUID, name: str, description: str | None = None, is_demo: bool = False):
        action = "k10.create_plan"
        self._auth(principal, action, f"organization_plan:school:{school_id}", school_id)
        obj = self.repo.create_plan(school_id=school_id, name=name, description=description, is_demo=is_demo)
        audit_write(self.db, principal, action, f"organization_plan:{obj.id}", None, "success")
        return obj

    def assign_task(self, principal: Principal, *, school_id: uuid.UUID, task_id: uuid.UUID, assignee_user_id: uuid.UUID, role_in_task: str | None = None, is_demo: bool = False):
        action = "k10.assign_task"
        self._auth(principal, action, f"organization_task:{task_id}", school_id)
        from app.modules.k10_organization_center.domain.models import OrgTask
        from app.shared.identity import User
        task = self.db.get(OrgTask, task_id)
        assignee = self.db.get(User, assignee_user_id)
        if task is None or task.school_id != school_id:
            raise ValueError("task_not_found_in_school")
        if assignee is None or assignee.school_id != school_id or not assignee.is_active:
            raise ValueError("assignee_not_found_in_school")
        obj = self.repo.add_assignment(school_id=school_id, task_id=task_id, assignee_user_id=assignee_user_id, role_in_task=role_in_task, is_demo=is_demo)
        audit_write(self.db, principal, action, f"organization_assignment:{obj.id}", None, "success")
        return obj

    def list_tasks(self, principal: Principal, school_id: uuid.UUID):
        action = "k10.list_tasks"
        self._auth(principal, action, f"organization_task:school:{school_id}", school_id)
        rows = self.repo.list_tasks(school_id)
        audit_write(self.db, principal, action, f"organization_task:school:{school_id}", None, "success", {"count": len(rows)})
        return rows

    def list_plans(self, principal: Principal, school_id: uuid.UUID):
        action = "k10.list_plans"
        self._auth(principal, action, f"organization_plan:school:{school_id}", school_id)
        rows = self.repo.list_plans(school_id)
        audit_write(self.db, principal, action, f"organization_plan:school:{school_id}", None, "success", {"count": len(rows)})
        return rows

    def list_assignments(self, principal: Principal, task_id: uuid.UUID, school_id: uuid.UUID):
        action = "k10.list_assignments"
        self._auth(principal, action, f"organization_task:{task_id}", school_id)
        rows = self.repo.list_assignments_for_task(task_id)
        audit_write(self.db, principal, action, f"organization_task:{task_id}", None, "success", {"count": len(rows)})
        return rows
