import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class TopicProgressKind(str, enum.Enum):
    COVERED = "covered"  # prebrate
    PRACTICED = "practiced"  # precvicene
    VERIFIED = "verified"  # overene


class TopicProgressStatus(str, enum.Enum):
    IN_PROGRESS_PRACTICE = "in_progress_practice"  # prebiehajuce precvicovanie
    PARTIALLY_MASTERED = "partially_mastered"  # ciastocne zvladnute
    VERIFIED_MASTERY = "verified_mastery"  # overene zvladnutie


class TopicState(Base, ValidityMixin):
    __tablename__ = "progress_topic_state"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("curriculum_topic.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(Enum(TopicProgressKind, name="progress_topic_kind", native_enum=False), nullable=False)
    status: Mapped[str] = mapped_column(Enum(TopicProgressStatus, name="progress_topic_status", native_enum=False), nullable=False)
    evidence_attempt_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_verification_evidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
