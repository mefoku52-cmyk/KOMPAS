from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k10_organization_center.domain.models import OrgAssignment, OrgPlan, OrgTask


class K10Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, *, school_id: uuid.UUID, title: str, description: str | None = None, status: str = "open", due_at=None, is_demo: bool = False) -> OrgTask:
        obj = OrgTask(school_id=school_id, title=title, description=description, status=status, due_at=due_at, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def create_plan(self, *, school_id: uuid.UUID, name: str, description: str | None = None, is_demo: bool = False) -> OrgPlan:
        obj = OrgPlan(school_id=school_id, name=name, description=description, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def add_assignment(self, *, school_id: uuid.UUID, task_id: uuid.UUID, assignee_user_id: uuid.UUID, role_in_task: str | None = None, is_demo: bool = False) -> OrgAssignment:
        obj = OrgAssignment(school_id=school_id, task_id=task_id, assignee_user_id=assignee_user_id, role_in_task=role_in_task, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_tasks(self, school_id: uuid.UUID):
        stmt = select(OrgTask).where(OrgTask.school_id == school_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_plans(self, school_id: uuid.UUID):
        stmt = select(OrgPlan).where(OrgPlan.school_id == school_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_assignments_for_task(self, task_id: uuid.UUID):
        stmt = select(OrgAssignment).where(OrgAssignment.task_id == task_id)
        return list(self.db.execute(stmt).scalars().all())
