import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class ClassTeacherAssignment(Base, ValidityMixin):
    __tablename__ = "school_class_teacher"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_class_group.id"), nullable=False, index=True)
    teacher_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("school_id", "class_group_id", "teacher_user_id", name="uq_school_class_teacher"),
    )
