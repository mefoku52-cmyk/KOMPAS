import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class School(Base, ValidityMixin):
    __tablename__ = "school_school"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class SchoolYear(Base, ValidityMixin):
    __tablename__ = "school_year"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_school_year_school_name"),)


class ClassGroup(Base, ValidityMixin):
    __tablename__ = "school_class_group"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    school_year_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_year.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("school_year_id", "name", name="uq_school_class_year_name"),)


class Enrollment(Base, ValidityMixin):
    __tablename__ = "school_enrollment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    school_year_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_year.id"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_class_group.id"), nullable=False, index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("school_year_id", "student_user_id", name="uq_school_enrollment_year_student"),
    )
