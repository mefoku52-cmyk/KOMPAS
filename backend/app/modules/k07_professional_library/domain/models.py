import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class LibraryItem(Base, ValidityMixin):
    __tablename__ = "teacher_workspace_library_item"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    owner_teacher_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class LibraryVersion(Base, ValidityMixin):
    __tablename__ = "teacher_workspace_library_version"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("teacher_workspace_library_item.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (UniqueConstraint("item_id", "version_number", name="uq_teacher_workspace_library_item_version"),)


class LibraryTag(Base, ValidityMixin):
    __tablename__ = "teacher_workspace_library_tag"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("teacher_workspace_library_item.id"), nullable=False, index=True)
    tag: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("item_id", "tag", name="uq_teacher_workspace_library_item_tag"),)
