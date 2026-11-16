from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k01_learning_profile.domain.models import StudentLearningProfile


class K01Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_profile(
        self,
        *,
        school_id: uuid.UUID,
        student_user_id: uuid.UUID,
        school_year_id: uuid.UUID,
        grade: int,
        label: str | None = None,
        version: int = 1,
        is_demo: bool = False,
    ) -> StudentLearningProfile:
        obj = StudentLearningProfile(
            school_id=school_id,
            student_user_id=student_user_id,
            school_year_id=school_year_id,
            grade=grade,
            label=label,
            version=version,
            is_demo=is_demo,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_history(self, student_user_id: uuid.UUID, school_id: Optional[uuid.UUID] = None) -> list[StudentLearningProfile]:
        stmt = select(StudentLearningProfile).where(StudentLearningProfile.student_user_id == student_user_id)
        if school_id is not None:
            stmt = stmt.where(StudentLearningProfile.school_id == school_id)
        stmt = stmt.order_by(StudentLearningProfile.valid_from.asc(), StudentLearningProfile.version.asc())
        return list(self.db.execute(stmt).scalars().all())

    def list_for_year(
        self, student_user_id: uuid.UUID, school_year_id: uuid.UUID, school_id: Optional[uuid.UUID] = None
    ) -> list[StudentLearningProfile]:
        stmt = select(StudentLearningProfile).where(
            StudentLearningProfile.student_user_id == student_user_id,
            StudentLearningProfile.school_year_id == school_year_id,
        )
        if school_id is not None:
            stmt = stmt.where(StudentLearningProfile.school_id == school_id)
        stmt = stmt.order_by(StudentLearningProfile.version.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_latest_for_year(
        self, student_user_id: uuid.UUID, school_year_id: uuid.UUID, school_id: Optional[uuid.UUID] = None
    ) -> Optional[StudentLearningProfile]:
        rows = self.list_for_year(student_user_id, school_year_id, school_id)
        return rows[-1] if rows else None
