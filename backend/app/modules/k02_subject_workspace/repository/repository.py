from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k02_subject_workspace.domain.models import SubjectWorkspace, WorkspaceTopicNode


class K02Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_workspace(
        self,
        *,
        school_id: uuid.UUID,
        subject_id: uuid.UUID,
        teacher_user_id: uuid.UUID,
        name: str,
        is_demo: bool = False,
    ) -> SubjectWorkspace:
        obj = SubjectWorkspace(
            school_id=school_id,
            subject_id=subject_id,
            teacher_user_id=teacher_user_id,
            name=name,
            is_demo=is_demo,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_workspace(self, workspace_id: uuid.UUID) -> Optional[SubjectWorkspace]:
        return self.db.get(SubjectWorkspace, workspace_id)

    def list_workspaces_for_teacher(self, teacher_user_id: uuid.UUID, school_id: Optional[uuid.UUID] = None):
        stmt = select(SubjectWorkspace).where(SubjectWorkspace.teacher_user_id == teacher_user_id)
        if school_id is not None:
            stmt = stmt.where(SubjectWorkspace.school_id == school_id)
        return list(self.db.execute(stmt).scalars().all())

    def add_node(
        self,
        *,
        school_id: uuid.UUID,
        workspace_id: uuid.UUID,
        title: str,
        topic_id: uuid.UUID | None = None,
        parent_node_id: uuid.UUID | None = None,
        order_index: int = 0,
        is_demo: bool = False,
    ) -> WorkspaceTopicNode:
        obj = WorkspaceTopicNode(
            school_id=school_id,
            workspace_id=workspace_id,
            topic_id=topic_id,
            parent_node_id=parent_node_id,
            title=title,
            order_index=order_index,
            is_demo=is_demo,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_nodes(self, workspace_id: uuid.UUID) -> list[WorkspaceTopicNode]:
        stmt = (
            select(WorkspaceTopicNode)
            .where(WorkspaceTopicNode.workspace_id == workspace_id)
            .order_by(WorkspaceTopicNode.parent_node_id.asc().nullsfirst(), WorkspaceTopicNode.order_index.asc(), WorkspaceTopicNode.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_node(self, node_id: uuid.UUID) -> Optional[WorkspaceTopicNode]:
        return self.db.get(WorkspaceTopicNode, node_id)
