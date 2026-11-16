from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k03_adaptive_learning.domain.models import AdaptiveRecommendation


class K03Repository:
    def __init__(self, db: Session):
        self.db = db

    def add_recommendation(self, *, school_id: uuid.UUID, student_user_id: uuid.UUID, topic_id: uuid.UUID, reason: str, suggested_action: str = "practice", is_demo: bool = False) -> AdaptiveRecommendation:
        obj = AdaptiveRecommendation(school_id=school_id, student_user_id=student_user_id, topic_id=topic_id, reason=reason, suggested_action=suggested_action, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_for_student(self, student_user_id: uuid.UUID, school_id: uuid.UUID | None = None) -> list[AdaptiveRecommendation]:
        stmt = select(AdaptiveRecommendation).where(AdaptiveRecommendation.student_user_id == student_user_id)
        if school_id is not None:
            stmt = stmt.where(AdaptiveRecommendation.school_id == school_id)
        stmt = stmt.order_by(AdaptiveRecommendation.valid_from.desc())
        return list(self.db.execute(stmt).scalars().all())
