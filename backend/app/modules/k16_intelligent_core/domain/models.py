import uuid

from sqlalchemy import Boolean, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class AiKnowledgeSource(Base, ValidityMixin):
    __tablename__ = "ai_knowledge_source"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AiContextMemory(Base, ValidityMixin):
    __tablename__ = "ai_knowledge_context_memory"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_record_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
