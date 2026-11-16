from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k02_subject_workspace.repository.repository import K02Repository
from app.shared.types import Principal, Role


class K02Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K02Repository(db)

    def _deny_or_ok(self, principal: Principal, action: str, resource: str, context: dict, purpose: str | None = None):
        decision = authorize(principal, action, resource, context=context, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, purpose, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        return decision

    def _owner_context(self, principal: Principal, workspace):
        if principal.is_system:
            return {"school_id": workspace.school_id, "system_internal": True}
        if principal.role == Role.TEACHER and principal.user_id == workspace.teacher_user_id:
            return {"scope": Scope.SELF.value, "owner_user_id": workspace.teacher_user_id, "school_id": workspace.school_id}
        if principal.role == Role.LEADERSHIP and principal.school_id == workspace.school_id:
            # read access for leadership only with purpose handled by caller
            return None
        return {"school_id": workspace.school_id}

    def create_workspace(self, principal: Principal, *, school_id: uuid.UUID, subject_id: uuid.UUID, teacher_user_id: uuid.UUID, name: str, is_demo: bool = False):
        action = "k02.create_workspace"
        resource = f"curriculum_subject_workspace:teacher:{teacher_user_id}"
        if principal.is_system:
            ctx = {"school_id": school_id, "system_internal": True}
        elif principal.role == Role.TEACHER and principal.user_id == teacher_user_id:
            ctx = {"scope": Scope.SELF.value, "owner_user_id": teacher_user_id, "school_id": school_id}
        else:
            ctx = {"school_id": school_id}
        self._deny_or_ok(principal, action, resource, ctx)
        ws = self.repo.create_workspace(school_id=school_id, subject_id=subject_id, teacher_user_id=teacher_user_id, name=name, is_demo=is_demo)
        audit_write(self.db, principal, action, f"curriculum_subject_workspace:{ws.id}", None, "success")
        return ws

    def get_workspace(self, principal: Principal, workspace_id: uuid.UUID, purpose: str | None = None):
        action = "k02.get_workspace"
        ws = self.repo.get_workspace(workspace_id)
        if not ws:
            raise ValueError("workspace_not_found")
        resource = f"curriculum_subject_workspace:{workspace_id}"
        if principal.is_system:
            ctx = {"school_id": ws.school_id, "system_internal": True}
        elif principal.role == Role.TEACHER and principal.user_id == ws.teacher_user_id:
            ctx = {"scope": Scope.SELF.value, "owner_user_id": ws.teacher_user_id, "school_id": ws.school_id}
        elif principal.role == Role.LEADERSHIP and principal.school_id == ws.school_id and purpose:
            ctx = {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": ws.school_id, "purpose": purpose}
        else:
            ctx = {"school_id": ws.school_id}
        self._deny_or_ok(principal, action, resource, ctx, purpose=purpose)
        audit_write(self.db, principal, action, resource, purpose, "success")
        return ws

    def list_workspaces(self, principal: Principal, teacher_user_id: uuid.UUID, school_id: uuid.UUID, purpose: str | None = None):
        action = "k02.list_workspaces"
        resource = f"curriculum_subject_workspace:teacher:{teacher_user_id}"
        if principal.is_system:
            ctx = {"school_id": school_id, "system_internal": True}
        elif principal.role == Role.TEACHER and principal.user_id == teacher_user_id:
            ctx = {"scope": Scope.SELF.value, "owner_user_id": teacher_user_id, "school_id": school_id}
        elif principal.role == Role.LEADERSHIP and principal.school_id == school_id and purpose:
            ctx = {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": school_id, "purpose": purpose}
        else:
            ctx = {"school_id": school_id}
        self._deny_or_ok(principal, action, resource, ctx, purpose=purpose)
        rows = self.repo.list_workspaces_for_teacher(teacher_user_id, school_id)
        audit_write(self.db, principal, action, resource, purpose, "success", {"count": len(rows)})
        return rows

    def add_node(self, principal: Principal, workspace_id: uuid.UUID, *, title: str, topic_id: uuid.UUID | None = None, parent_node_id: uuid.UUID | None = None, order_index: int = 0, is_demo: bool = False):
        action = "k02.add_node"
        ws = self.repo.get_workspace(workspace_id)
        if not ws:
            raise ValueError("workspace_not_found")
        resource = f"curriculum_subject_workspace:{workspace_id}"
        if principal.is_system:
            ctx = {"school_id": ws.school_id, "system_internal": True}
        elif principal.role == Role.TEACHER and principal.user_id == ws.teacher_user_id:
            ctx = {"scope": Scope.SELF.value, "owner_user_id": ws.teacher_user_id, "school_id": ws.school_id}
        else:
            ctx = {"school_id": ws.school_id}
        self._deny_or_ok(principal, action, resource, ctx)
        node = self.repo.add_node(
            school_id=ws.school_id,
            workspace_id=workspace_id,
            title=title,
            topic_id=topic_id,
            parent_node_id=parent_node_id,
            order_index=order_index,
            is_demo=is_demo,
        )
        audit_write(self.db, principal, action, f"curriculum_workspace_topic_node:{node.id}", None, "success")
        return node

    def list_nodes(self, principal: Principal, workspace_id: uuid.UUID, purpose: str | None = None):
        action = "k02.list_nodes"
        ws = self.repo.get_workspace(workspace_id)
        if not ws:
            raise ValueError("workspace_not_found")
        resource = f"curriculum_subject_workspace:{workspace_id}"
        if principal.is_system:
            ctx = {"school_id": ws.school_id, "system_internal": True}
        elif principal.role == Role.TEACHER and principal.user_id == ws.teacher_user_id:
            ctx = {"scope": Scope.SELF.value, "owner_user_id": ws.teacher_user_id, "school_id": ws.school_id}
        elif principal.role == Role.LEADERSHIP and principal.school_id == ws.school_id and purpose:
            ctx = {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": ws.school_id, "purpose": purpose}
        else:
            ctx = {"school_id": ws.school_id}
        self._deny_or_ok(principal, action, resource, ctx, purpose=purpose)
        rows = self.repo.list_nodes(workspace_id)
        audit_write(self.db, principal, action, resource, purpose, "success", {"count": len(rows)})
        return rows
