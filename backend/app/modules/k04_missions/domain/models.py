import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class TaskType(str, enum.Enum):
    CHOICE = "choice"
    NUMERIC = "numeric"
    TEXT_MATCH = "text_match"


class Mission(Base, ValidityMixin):
    __tablename__ = "learning_mission"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("curriculum_topic.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MissionTask(Base, ValidityMixin):
    __tablename__ = "learning_task"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    mission_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("learning_mission.id"), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(Enum(TaskType, name="learning_task_type", native_enum=False), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class MissionAttempt(Base, ValidityMixin):
    __tablename__ = "learning_attempt"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("learning_task.id"), nullable=False, index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evaluated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
