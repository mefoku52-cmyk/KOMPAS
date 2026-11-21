from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.database.session import Base
from app.core.permissions.policy import Scope, authorize
from app.modules.k03_adaptive_learning.repository.repository import K03Repository
from app.shared.progress import resolve_effective_states, status_value
from app.shared.types import Principal, Role


class K03Service:
    """Deterministic, explainable recommendations from K-05 states. No personality inference."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = K03Repository(db)

    def _authorize_or_raise(self, principal: Principal, action: str, resource: str, context: dict, purpose: str | None = None):
        decision = authorize(principal, action, resource, context=context, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, purpose, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def _view_context(self, principal: Principal, *, student_user_id: uuid.UUID, school_id: uuid.UUID, purpose: str | None = None, class_group_id: uuid.UUID | None = None, teaches: bool = False):
        if principal.is_system:
            return {"school_id": school_id, "system_internal": True}
        if principal.user_id == student_user_id:
            return {"scope": Scope.SELF.value, "owner_user_id": student_user_id, "student_user_id": student_user_id, "school_id": school_id}
        if principal.role == Role.PARENT:
            return {"scope": Scope.GUARDIAN_OF.value, "student_user_id": student_user_id, "child_user_id": student_user_id, "school_id": school_id}
        if principal.role == Role.TEACHER:
            return {"scope": Scope.TEACHES_CLASS.value, "student_user_id": student_user_id, "class_group_id": class_group_id, "teacher_user_id": principal.user_id if teaches else None, "teaches": teaches, "school_id": school_id}
        if principal.role == Role.LEADERSHIP:
            return {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": school_id, "student_user_id": student_user_id, "purpose": purpose}
        return {"school_id": school_id}

    def _status_value(self, value: Any) -> str:
        return status_value(value)

    def recommend_for_student(self, principal: Principal, *, school_id: uuid.UUID, student_user_id: uuid.UUID, purpose: str | None = None, class_group_id: uuid.UUID | None = None, teaches: bool = False, persist: bool = False, is_demo: bool = False):
        action = "k03.recommend"
        resource = f"progress_adaptive_recommendation:student:{student_user_id}"
        ctx = self._view_context(principal, student_user_id=student_user_id, school_id=school_id, purpose=purpose, class_group_id=class_group_id, teaches=teaches)
        self._authorize_or_raise(principal, action, resource, ctx, purpose=purpose)

        topic_state_table = Base.metadata.tables.get("progress_topic_state")
        suggestions: list[dict[str, Any]] = []
        if topic_state_table is not None:
            stmt = select(
                topic_state_table.c.topic_id,
                topic_state_table.c.kind,
                topic_state_table.c.status,
                topic_state_table.c.evidence_attempt_ref,
                topic_state_table.c.valid_from,
                topic_state_table.c.version,
            ).where(
                topic_state_table.c.student_user_id == student_user_id,
                topic_state_table.c.school_id == school_id,
            )
            rows = self.db.execute(stmt).all()
            effective = resolve_effective_states(rows, key=lambda r: r.topic_id)
            latest_by_topic: list[tuple[Any, Any]] = sorted(
                effective.items(), key=lambda item: item[1].valid_from, reverse=True
            )
        else:
            latest_by_topic = []

        for topic_id, row in latest_by_topic:
            st = {
                "status": self._status_value(row.status),
                "evidence_attempt_ref": row.evidence_attempt_ref,
            }
            status = st["status"]
            if status == "verified_mastery":
                continue
            evidence = st.get("evidence_attempt_ref") or "bez odkazu"
            if status == "in_progress_practice":
                reason = f"Deterministic: tema ma stav {status} na zaklade dokladu {evidence}; odporuca sa pokracovat v precvicovani."
            else:
                reason = f"Deterministic: tema ma stav {status} (ciastocne zvladnute) na zaklade dokladu {evidence}; odporuca sa cielene precvicovanie pred overenim."
            suggestions.append({"topic_id": str(topic_id), "reason": reason, "suggested_action": "practice"})
            if persist:
                self.repo.add_recommendation(
                    school_id=school_id, student_user_id=student_user_id, topic_id=topic_id,
                    reason=reason, suggested_action="practice", is_demo=is_demo
                )
        audit_write(self.db, principal, action, resource, purpose, "success", {"count": len(suggestions), "persisted": persist})
        return suggestions
