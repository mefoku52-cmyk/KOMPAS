from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.session import Base
from app.shared.school import Enrollment


class K09Repository:
    def __init__(self, db: Session):
        self.db = db

    def list_student_ids_in_class(self, school_id: uuid.UUID, class_group_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(Enrollment.student_user_id).where(
            Enrollment.school_id == school_id,
            Enrollment.class_group_id == class_group_id,
        )
        return [row[0] for row in self.db.execute(stmt).all()]

    def get_topic_state_distribution(
        self,
        school_id: uuid.UUID,
        student_user_ids: list[uuid.UUID],
        topic_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        if not student_user_ids:
            return {"total_students": 0, "by_status": {}, "by_kind": {}, "by_topic": {}}
        table = Base.metadata.tables.get("progress_topic_state")
        if table is None:
            return {"total_students": len(set(student_user_ids)), "by_status": {}, "by_kind": {}, "by_topic": {}}

        stmt = select(
            table.c.student_user_id,
            table.c.topic_id,
            table.c.kind,
            table.c.status,
            table.c.valid_from,
            table.c.version,
        ).where(
            table.c.school_id == school_id,
            table.c.student_user_id.in_(student_user_ids),
        )
        if topic_id is not None:
            stmt = stmt.where(table.c.topic_id == topic_id)
        rows = self.db.execute(stmt).all()

        latest: dict[tuple[uuid.UUID, uuid.UUID], Any] = {}
        for r in rows:
            key = (r.student_user_id, r.topic_id)
            prev = latest.get(key)
            if prev is None or (r.valid_from, r.version) > (prev.valid_from, prev.version):
                latest[key] = r

        by_status: dict[str, int] = defaultdict(int)
        by_kind: dict[str, int] = defaultdict(int)
        by_topic: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in latest.values():
            status = getattr(r.status, "value", r.status)
            kind = getattr(r.kind, "value", r.kind)
            by_status[status] += 1
            by_kind[kind] += 1
            by_topic[str(r.topic_id)][status] += 1

        return {
            "total_students": len(set(student_user_ids)),
            "tracked_student_topic_pairs": len(latest),
            "by_status": dict(by_status),
            "by_kind": dict(by_kind),
            "by_topic": {k: dict(v) for k, v in by_topic.items()},
        }
