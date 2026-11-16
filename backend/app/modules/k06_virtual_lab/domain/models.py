import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class SimulationDefinition(Base, ValidityMixin):
    __tablename__ = "learning_simulation_definition"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=True, index=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    param_schema: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON text
    compute_key: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SimulationRun(Base, ValidityMixin):
    __tablename__ = "learning_simulation_run"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    definition_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("learning_simulation_definition.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    inputs: Mapped[str] = mapped_column(Text, nullable=False)  # JSON text
    outputs: Mapped[str] = mapped_column(Text, nullable=False)  # JSON text
