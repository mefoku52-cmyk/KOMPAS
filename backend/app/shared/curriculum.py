import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class Subject(Base, ValidityMixin):
    __tablename__ = "curriculum_subject"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_curriculum_subject_school_name"),)


class Topic(Base, ValidityMixin):
    __tablename__ = "curriculum_topic"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("curriculum_subject.id"), nullable=False, index=True)
    parent_topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("curriculum_topic.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("subject_id", "parent_topic_id", "name", name="uq_curriculum_topic_subject_parent_name"),
    )
