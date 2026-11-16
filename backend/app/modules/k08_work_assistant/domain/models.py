import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class DraftStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED_FOR_APPROVAL = "submitted_for_approval"
    APPROVED = "approved"


class WorkAssistantDraft(Base, ValidityMixin):
    __tablename__ = "teacher_workspace_assistant_draft"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    teacher_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    draft_type: Mapped[str] = mapped_column(String(32), nullable=False)  # worksheet | test
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Enum(DraftStatus, name="teacher_workspace_draft_status", native_enum=False), nullable=False, default=DraftStatus.DRAFT.value)
    source_refs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
