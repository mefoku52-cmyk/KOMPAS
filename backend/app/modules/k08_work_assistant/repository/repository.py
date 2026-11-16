from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k08_work_assistant.domain.models import DraftStatus, WorkAssistantDraft


class K08Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_draft(self, *, school_id: uuid.UUID, teacher_user_id: uuid.UUID, title: str, draft_type: str, content: str, source_refs: str | None = None, is_demo: bool = False) -> WorkAssistantDraft:
        obj = WorkAssistantDraft(school_id=school_id, teacher_user_id=teacher_user_id, title=title, draft_type=draft_type, content=content, status=DraftStatus.DRAFT.value, source_refs=source_refs, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_draft(self, draft_id: uuid.UUID) -> WorkAssistantDraft | None:
        return self.db.get(WorkAssistantDraft, draft_id)

    def set_status(self, draft: WorkAssistantDraft, status: DraftStatus) -> WorkAssistantDraft:
        draft.status = status.value if isinstance(status, DraftStatus) else status
        self.db.flush()
        return draft

    def list_for_teacher(self, school_id: uuid.UUID, teacher_user_id: uuid.UUID):
        stmt = select(WorkAssistantDraft).where(WorkAssistantDraft.school_id == school_id, WorkAssistantDraft.teacher_user_id == teacher_user_id)
        return list(self.db.execute(stmt).scalars().all())
