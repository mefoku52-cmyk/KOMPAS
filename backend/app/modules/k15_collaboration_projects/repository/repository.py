from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k15_collaboration_projects.domain.models import CollaborationProject, ProjectMember, ProjectSubmission, ProjectTask


class K15Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, *, school_id: uuid.UUID, title: str, description: str | None, owner_user_id: uuid.UUID, status: str = "active", is_demo: bool = False) -> CollaborationProject:
        p = CollaborationProject(school_id=school_id, title=title, description=description, owner_user_id=owner_user_id, status=status, is_demo=is_demo)
        self.db.add(p)
        self.db.flush()
        return p

    def add_member(self, *, school_id: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID, role: str = "member", is_demo: bool = False) -> ProjectMember:
        m = ProjectMember(school_id=school_id, project_id=project_id, user_id=user_id, role=role, is_demo=is_demo)
        self.db.add(m)
        self.db.flush()
        return m

    def get_project(self, project_id: uuid.UUID) -> CollaborationProject | None:
        return self.db.get(CollaborationProject, project_id)

    def is_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(ProjectMember.id).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        return self.db.execute(stmt).first() is not None

    def create_task(self, *, school_id: uuid.UUID, project_id: uuid.UUID, title: str, description: str | None, assignee_user_id: uuid.UUID | None, status: str = "open", is_demo: bool = False) -> ProjectTask:
        t = ProjectTask(school_id=school_id, project_id=project_id, title=title, description=description, assignee_user_id=assignee_user_id, status=status, is_demo=is_demo)
        self.db.add(t)
        self.db.flush()
        return t

    def get_task(self, task_id: uuid.UUID) -> ProjectTask | None:
        return self.db.get(ProjectTask, task_id)

    def create_submission(self, *, school_id: uuid.UUID, task_id: uuid.UUID, submitted_by_user_id: uuid.UUID, content: str, status: str = "submitted", is_demo: bool = False) -> ProjectSubmission:
        s = ProjectSubmission(school_id=school_id, task_id=task_id, submitted_by_user_id=submitted_by_user_id, content=content, status=status, is_demo=is_demo)
        self.db.add(s)
        self.db.flush()
        return s

    def list_tasks(self, project_id: uuid.UUID) -> list[ProjectTask]:
        return list(self.db.execute(select(ProjectTask).where(ProjectTask.project_id == project_id)).scalars().all())

    def list_submissions(self, task_id: uuid.UUID) -> list[ProjectSubmission]:
        return list(self.db.execute(select(ProjectSubmission).where(ProjectSubmission.task_id == task_id)).scalars().all())
