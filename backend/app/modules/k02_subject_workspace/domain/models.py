import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class SubjectWorkspace(Base, ValidityMixin):
    __tablename__ = "curriculum_subject_workspace"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("curriculum_subject.id"), nullable=False, index=True)
    teacher_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("subject_id", "teacher_user_id", name="uq_curriculum_workspace_subject_teacher"),
    )


class WorkspaceTopicNode(Base, ValidityMixin):
    __tablename__ = "curriculum_workspace_topic_node"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("curriculum_subject_workspace.id"), nullable=False, index=True)
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("curriculum_topic.id"), nullable=True, index=True)
    parent_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("curriculum_workspace_topic_node.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
