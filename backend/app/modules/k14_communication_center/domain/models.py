import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class CommunicationThread(Base, ValidityMixin):
    __tablename__ = "communication_thread"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)


class CommunicationParticipant(Base, ValidityMixin):
    __tablename__ = "communication_thread_participant"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("communication_thread.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("thread_id", "user_id", name="uq_communication_thread_user"),)


class CommunicationMessage(Base, ValidityMixin):
    __tablename__ = "communication_message"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("communication_thread.id"), nullable=False, index=True)
    sender_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
