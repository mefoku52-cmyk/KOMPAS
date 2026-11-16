from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k05_knowledge_continuity.domain.models import TopicState


class K05Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_state(
        self,
        *,
        school_id: uuid.UUID,
        student_user_id: uuid.UUID,
        topic_id: uuid.UUID,
        kind: str,
        status: str,
        evidence_attempt_ref: str | None = None,
        is_verification_evidence: bool = False,
        version: int = 1,
        is_demo: bool = False,
    ) -> TopicState:
        obj = TopicState(
            school_id=school_id,
            student_user_id=student_user_id,
            topic_id=topic_id,
            kind=kind,
            status=status,
            evidence_attempt_ref=evidence_attempt_ref,
            is_verification_evidence=is_verification_evidence,
            version=version,
            is_demo=is_demo,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_states(self, student_user_id: uuid.UUID, topic_id: uuid.UUID | None = None, school_id: uuid.UUID | None = None) -> list[TopicState]:
        stmt = select(TopicState).where(TopicState.student_user_id == student_user_id)
        if topic_id is not None:
            stmt = stmt.where(TopicState.topic_id == topic_id)
        if school_id is not None:
            stmt = stmt.where(TopicState.school_id == school_id)
        stmt = stmt.order_by(TopicState.valid_from.asc(), TopicState.version.asc())
        return list(self.db.execute(stmt).scalars().all())
