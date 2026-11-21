from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.session import Base
from app.shared.progress import resolve_effective_states, status_value
from app.shared.school import ClassGroup, Enrollment


class K09Repository:
    def __init__(self, db: Session):
        self.db = db

    def list_classes_for_teacher(self, school_id: uuid.UUID, teacher_user_id: uuid.UUID) -> list[dict[str, Any]]:
        link = Base.metadata.tables.get("school_class_teacher")
        if link is None:
            return []
        stmt = (
            select(ClassGroup.id, ClassGroup.name, ClassGroup.grade, ClassGroup.school_year_id)
            .join(link, link.c.class_group_id == ClassGroup.id)
            .where(link.c.school_id == school_id, link.c.teacher_user_id == teacher_user_id)
            .order_by(ClassGroup.name)
        )
        rows = self.db.execute(stmt).all()
        counts = {
            str(cid): self.db.execute(
                select(Enrollment.student_user_id).where(
                    Enrollment.school_id == school_id, Enrollment.class_group_id == cid
                )
            ).all()
            for cid in [r[0] for r in rows]
        }
        return [
            {
                "class_group_id": str(r[0]),
                "name": r[1],
                "grade": r[2],
                "school_year_id": str(r[3]),
                "student_count": len(counts.get(str(r[0]), [])),
            }
            for r in rows
        ]

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

        latest = resolve_effective_states(rows, key=lambda r: (r.student_user_id, r.topic_id))

        by_status: dict[str, int] = defaultdict(int)
        by_kind: dict[str, int] = defaultdict(int)
        by_topic: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in latest.values():
            status = status_value(r.status)
            kind = status_value(r.kind)
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
