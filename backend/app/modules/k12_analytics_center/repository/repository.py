from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.session import Base
from app.modules.k12_analytics_center.domain.models import AnalyticsAggregateSnapshot
from app.shared.school import Enrollment


class K12Repository:
    def __init__(self, db: Session):
        self.db = db

    def list_student_ids_in_school(self, school_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(Enrollment.student_user_id).where(Enrollment.school_id == school_id)
        return [row[0] for row in self.db.execute(stmt).all()]

    def get_latest_topic_states(self, school_id: uuid.UUID, student_user_ids: list[uuid.UUID] | None = None):
        table = Base.metadata.tables.get("progress_topic_state")
        if table is None:
            return []
        stmt = select(table).where(table.c.school_id == school_id)
        if student_user_ids is not None:
            if not student_user_ids:
                return []
            stmt = stmt.where(table.c.student_user_id.in_(student_user_ids))
        rows = self.db.execute(stmt).all()
        latest: dict[tuple[Any, Any], Any] = {}
        for r in rows:
            key = (r.student_user_id, r.topic_id)
            prev = latest.get(key)
            if prev is None or (r.valid_from, r.version) > (prev.valid_from, prev.version):
                latest[key] = r
        return list(latest.values())

    def aggregate_school(self, school_id: uuid.UUID) -> dict[str, Any]:
        student_ids = set(self.list_student_ids_in_school(school_id))
        rows = self.get_latest_topic_states(school_id)
        by_status: dict[str, int] = defaultdict(int)
        by_kind: dict[str, int] = defaultdict(int)
        by_topic: dict[str, int] = defaultdict(int)
        for r in rows:
            status = getattr(r.status, "value", r.status)
            kind = getattr(r.kind, "value", r.kind)
            by_status[str(status)] += 1
            by_kind[str(kind)] += 1
            by_topic[str(r.topic_id)] += 1
        return {
            "total_students": len(student_ids),
            "tracked_pairs": len(rows),
            "by_status": dict(by_status),
            "by_kind": dict(by_kind),
            "by_topic": dict(by_topic),
        }

    def save_snapshot(self, *, school_id: uuid.UUID, metric_key: str, group_key: str | None, group_size: int, suppressed: bool, value_count: int, is_demo: bool = False) -> AnalyticsAggregateSnapshot:
        obj = AnalyticsAggregateSnapshot(
            school_id=school_id,
            metric_key=metric_key,
            group_key=group_key,
            group_size=group_size,
            suppressed=1 if suppressed else 0,
            value_count=value_count,
            is_demo=is_demo,
        )
        self.db.add(obj)
        self.db.flush()
        return obj
