from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import AuditLog
from app.core.permissions.policy import Scope, authorize
from app.shared.types import Principal, Role


class AuditEngineService:
    """Read-only queries over audit log (writes only in core/audit)."""

    def __init__(self, db: Session):
        self.db = db

    def list_entries(self, principal: Principal, school_id: Optional[Any] = None, limit: int = 100):
        context = {"school_id": school_id, "system_internal": principal.is_system}
        if principal.role == Role.LEADERSHIP and principal.school_id == school_id:
            context = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": school_id}
        decision = authorize(principal, "audit.read", "audit_log", context=context)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        if school_id is not None:
            stmt = stmt.where(AuditLog.school_id == school_id)
        rows = self.db.execute(stmt).scalars().all()
        return rows

    def report(self, principal: Principal, school_id: Optional[Any] = None):
        rows = self.list_entries(principal, school_id=school_id, limit=1000)
        by_outcome: dict[str, int] = {}
        for r in rows:
            by_outcome[r.outcome] = by_outcome.get(r.outcome, 0) + 1
        return {"total": len(rows), "by_outcome": by_outcome}
