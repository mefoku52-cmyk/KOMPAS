import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class StudentLearningProfile(Base, ValidityMixin):
    __tablename__ = "progress_student_profile"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=False, index=True)
    school_year_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_year.id"), nullable=False, index=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "student_user_id",
            "school_year_id",
            "version",
            name="uq_progress_student_profile_student_year_version",
        ),
    )
