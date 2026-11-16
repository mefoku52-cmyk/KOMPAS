from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.modules.k15_collaboration_projects.repository.repository import K15Repository
from app.shared.types import Principal


class K15Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K15Repository(db)

    def _require_project_member(self, principal: Principal, project_id: uuid.UUID, action: str, resource: str):
        project = self.repo.get_project(project_id)
        if not project:
            raise ValueError("project_not_found")
        if principal.is_system:
            return project
        if principal.school_id != project.school_id or not self.repo.is_member(project_id, principal.user_id):
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": "not_member"})
            raise PermissionError("not_member")
        return project

    def create_project(self, principal: Principal, *, school_id: uuid.UUID, title: str, description: str | None = None, member_user_ids: list[uuid.UUID] | None = None, is_demo: bool = False):
        action = "k15.create_project"
        if not principal.is_system and principal.school_id != school_id:
            audit_write(self.db, principal, action, f"organization_project:school:{school_id}", None, "denied", {"reason": "wrong_school"})
            raise PermissionError("wrong_school")
        project = self.repo.create_project(school_id=school_id, title=title, description=description, owner_user_id=principal.user_id, is_demo=is_demo)
        # owner is member
        self.repo.add_member(school_id=school_id, project_id=project.id, user_id=principal.user_id, role="owner", is_demo=is_demo)
        for uid in (member_user_ids or []):
            if uid != principal.user_id:
                self.repo.add_member(school_id=school_id, project_id=project.id, user_id=uid, role="member", is_demo=is_demo)
        audit_write(self.db, principal, action, f"organization_project:{project.id}", None, "success")
        return project

    def add_member(self, principal: Principal, *, project_id: uuid.UUID, user_id: uuid.UUID, role: str = "member", is_demo: bool = False):
        action = "k15.add_member"
        resource = f"organization_project:{project_id}"
        project = self._require_project_member(principal, project_id, action, resource)
        # only owner can add (simple rule)
        if not principal.is_system and project.owner_user_id != principal.user_id:
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": "not_owner"})
            raise PermissionError("not_owner")
        m = self.repo.add_member(school_id=project.school_id, project_id=project.id, user_id=user_id, role=role, is_demo=is_demo)
        audit_write(self.db, principal, action, resource, None, "success", {"member": str(user_id)})
        return m

    def create_task(self, principal: Principal, *, project_id: uuid.UUID, title: str, description: str | None = None, assignee_user_id: uuid.UUID | None = None, is_demo: bool = False):
        action = "k15.create_task"
        resource = f"organization_project:{project_id}"
        project = self._require_project_member(principal, project_id, action, resource)
        t = self.repo.create_task(school_id=project.school_id, project_id=project.id, title=title, description=description, assignee_user_id=assignee_user_id, is_demo=is_demo)
        audit_write(self.db, principal, action, f"organization_project_task:{t.id}", None, "success")
        return t

    def submit(self, principal: Principal, *, task_id: uuid.UUID, content: str, is_demo: bool = False):
        action = "k15.submit"
        task = self.repo.get_task(task_id)
        if not task:
            raise ValueError("task_not_found")
        resource = f"organization_project_task:{task_id}"
        self._require_project_member(principal, task.project_id, action, resource)
        sub = self.repo.create_submission(school_id=task.school_id, task_id=task.id, submitted_by_user_id=principal.user_id, content=content, is_demo=is_demo)
        audit_write(self.db, principal, action, resource, None, "success", {"submission_id": str(sub.id)})
        return sub

    def list_tasks(self, principal: Principal, *, project_id: uuid.UUID):
        action = "k15.list_tasks"
        resource = f"organization_project:{project_id}"
        self._require_project_member(principal, project_id, action, resource)
        rows = self.repo.list_tasks(project_id)
        audit_write(self.db, principal, action, resource, None, "success", {"count": len(rows)})
        return rows

    def list_submissions(self, principal: Principal, *, task_id: uuid.UUID):
        action = "k15.list_submissions"
        task = self.repo.get_task(task_id)
        if not task:
            raise ValueError("task_not_found")
        resource = f"organization_project_task:{task_id}"
        self._require_project_member(principal, task.project_id, action, resource)
        rows = self.repo.list_submissions(task_id)
        audit_write(self.db, principal, action, resource, None, "success", {"count": len(rows)})
        return rows
