import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class OperationRequestStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class OperationRequest(Base, ValidityMixin):
    __tablename__ = "organization_operation_request"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    requester_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)  # room | equipment
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Enum(OperationRequestStatus, name="organization_operation_request_status", native_enum=False), nullable=False, default=OperationRequestStatus.SUBMITTED.value)
