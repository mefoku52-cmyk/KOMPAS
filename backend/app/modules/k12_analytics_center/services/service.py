from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.config.settings import settings
from app.core.permissions.policy import Scope, authorize
from app.modules.k12_analytics_center.repository.repository import K12Repository
from app.shared.types import Principal, Role


def _apply_threshold(counts: dict[str, int], threshold: int) -> dict[str, dict[str, int | bool]]:
    out: dict[str, dict[str, int | bool]] = {}
    for key, value in counts.items():
        suppressed = value < threshold
        out[key] = {"value": 0 if suppressed else value, "suppressed": suppressed}
    return out


class K12Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K12Repository(db)

    def _threshold(self) -> int:
        return int(getattr(settings, "analytics_min_group_size", 5))

    def _auth_school(self, principal: Principal, action: str, resource: str, school_id: uuid.UUID, purpose: str | None = None):
        if principal.is_system:
            return
        ctx = {"school_id": school_id}
        if principal.role == Role.LEADERSHIP and principal.school_id == school_id:
            ctx = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": school_id}
        elif principal.role == Role.TEACHER and principal.school_id == school_id:
            ctx = {"school_id": school_id}
        decision = authorize(principal, action, resource, context=ctx, db=self.db)
        if not decision.allowed:
            if principal.role == Role.TEACHER and principal.school_id == school_id:
                return
            audit_write(self.db, principal, action, resource, purpose, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def get_school_overview(self, principal: Principal, *, school_id: uuid.UUID):
        action = "k12.get_school_overview"
        resource = f"school:{school_id}:analytics"
        self._auth_school(principal, action, resource, school_id)
        raw = self.repo.aggregate_school(school_id)
        threshold = self._threshold()
        suppressed = raw["total_students"] < threshold
        if suppressed:
            payload = {
                "school_id": str(school_id),
                "suppressed": True,
                "threshold": threshold,
                "total_students": 0,
                "by_status": {},
                "by_kind": {},
                "by_topic": {},
            }
        else:
            payload = {
                "school_id": str(school_id),
                "suppressed": False,
                "threshold": threshold,
                "total_students": raw["total_students"],
                "tracked_pairs": raw["tracked_pairs"],
                "by_status": _apply_threshold(raw["by_status"], threshold),
                "by_kind": _apply_threshold(raw["by_kind"], threshold),
                "by_topic": _apply_threshold(raw["by_topic"], threshold),
            }
        audit_write(self.db, principal, action, resource, None, "success", {"suppressed": suppressed})
        return payload

    def get_individual_progress(self, principal: Principal, *, school_id: uuid.UUID, student_user_id: uuid.UUID, purpose: str | None):
        action = "k12.get_individual_progress"
        resource = f"student:{student_user_id}:progress"
        if not purpose:
            audit_write(self.db, principal, action, resource, purpose, "denied", {"reason": "purpose_required"})
            raise PermissionError("purpose_required")
        self._auth_school(principal, action, resource, school_id, purpose=purpose)
        rows = self.repo.get_latest_topic_states(school_id, [student_user_id])
        data = [
            {
                "topic_id": str(r.topic_id),
                "kind": getattr(r.kind, "value", r.kind),
                "status": getattr(r.status, "value", r.status),
                "version": r.version,
            }
            for r in rows
        ]
        audit_write(self.db, principal, action, resource, purpose, "success", {"count": len(data)})
        return {"student_user_id": str(student_user_id), "items": data}
