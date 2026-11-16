from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.session import Base
from app.shared.identity import GuardianLink


class K13Repository:
    def __init__(self, db: Session):
        self.db = db

    def list_linked_children(self, guardian_user_id: uuid.UUID, school_id: uuid.UUID | None = None) -> list[uuid.UUID]:
        stmt = select(GuardianLink.child_user_id).where(GuardianLink.guardian_user_id == guardian_user_id)
        if school_id is not None:
            stmt = stmt.where(GuardianLink.school_id == school_id)
        return [row[0] for row in self.db.execute(stmt).all()]

    def is_guardian_of(self, guardian_user_id: uuid.UUID, child_user_id: uuid.UUID, school_id: uuid.UUID | None = None) -> bool:
        stmt = select(GuardianLink.id).where(
            GuardianLink.guardian_user_id == guardian_user_id,
            GuardianLink.child_user_id == child_user_id,
        )
        if school_id is not None:
            stmt = stmt.where(GuardianLink.school_id == school_id)
        return self.db.execute(stmt).first() is not None

    def get_child_progress_summary(self, school_id: uuid.UUID, child_user_id: uuid.UUID) -> dict[str, Any]:
        table = Base.metadata.tables.get("progress_topic_state")
        if table is None:
            return {"tracked_pairs": 0, "by_status": {}, "by_kind": {}}
        rows = self.db.execute(
            select(table).where(table.c.school_id == school_id, table.c.student_user_id == child_user_id)
        ).all()
        latest: dict[Any, Any] = {}
        for r in rows:
            key = r.topic_id
            prev = latest.get(key)
            if prev is None or (r.valid_from, r.version) > (prev.valid_from, prev.version):
                latest[key] = r
        by_status: dict[str, int] = defaultdict(int)
        by_kind: dict[str, int] = defaultdict(int)
        for r in latest.values():
            status = getattr(r.status, "value", r.status)
            kind = getattr(r.kind, "value", r.kind)
            by_status[str(status)] += 1
            by_kind[str(kind)] += 1
        return {"tracked_pairs": len(latest), "by_status": dict(by_status), "by_kind": dict(by_kind)}

    def get_visible_teacher_notes(self, school_id: uuid.UUID, child_user_id: uuid.UUID) -> list[dict[str, Any]]:
        # Teacher private notes (TEACHER_PRIVATE_NOTE) must never be visible to parents.
        # No teacher-note table is modeled in current schema; return empty approved set.
        _ = (school_id, child_user_id)
        return []
