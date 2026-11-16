from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.shared.types import Principal


class AnalyticsEngineService:
    """Minimal event-to-aggregate processor stub for K-16."""

    def __init__(self, db: Session):
        self.db = db
        self._aggregates: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def process_event(self, principal: Principal, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, int]:
        payload = payload or {}
        self._aggregates[event_type]["count"] += 1
        audit_write(self.db, principal, "ai.analytics.process_event", event_type, None, "success", {"count": self._aggregates[event_type]["count"]})
        return dict(self._aggregates[event_type])
