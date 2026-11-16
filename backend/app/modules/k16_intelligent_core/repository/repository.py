from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k16_intelligent_core.domain.models import AiContextMemory, AiKnowledgeSource


class K16Repository:
    def __init__(self, db: Session):
        self.db = db

    # knowledge sources
    def create_source(
        self,
        *,
        school_id: uuid.UUID,
        name: str,
        source_type: str,
        content: str,
        approved: bool = False,
        is_demo: bool = False,
    ) -> AiKnowledgeSource:
        obj = AiKnowledgeSource(
            school_id=school_id,
            name=name,
            source_type=source_type,
            content=content,
            approved=approved,
            is_demo=is_demo,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_approved_sources(self, school_id: Optional[uuid.UUID] = None) -> list[AiKnowledgeSource]:
        stmt = select(AiKnowledgeSource).where(AiKnowledgeSource.approved.is_(True))
        if school_id is not None:
            stmt = stmt.where(AiKnowledgeSource.school_id == school_id)
        return list(self.db.execute(stmt).scalars().all())

    # context memory
    def create_context_memory(
        self,
        *,
        school_id: uuid.UUID,
        source_record_ref: str,
        content: str,
        is_demo: bool = False,
    ) -> AiContextMemory:
        if not source_record_ref or not str(source_record_ref).strip():
            raise ValueError("source_record_ref is required")
        obj = AiContextMemory(
            school_id=school_id,
            source_record_ref=source_record_ref,
            content=content,
            is_demo=is_demo,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_context_memories(self, school_id: Optional[uuid.UUID] = None) -> list[AiContextMemory]:
        stmt = select(AiContextMemory)
        if school_id is not None:
            stmt = stmt.where(AiContextMemory.school_id == school_id)
        return list(self.db.execute(stmt).scalars().all())
