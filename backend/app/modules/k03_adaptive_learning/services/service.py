from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k03_adaptive_learning.repository.repository import K03Repository
from app.modules.k05_knowledge_continuity.domain.models import TopicState, TopicProgressStatus
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

    def recommend_for_student(self, principal: Principal, *, school_id: uuid.UUID, student_user_id: uuid.UUID, purpose: str | None = None, class_group_id: uuid.UUID | None = None, teaches: bool = False, persist: bool = False, is_demo: bool = False):
        action = "k03.recommend"
        resource = f"progress_adaptive_recommendation:student:{student_user_id}"
        ctx = self._view_context(principal, student_user_id=student_user_id, school_id=school_id, purpose=purpose, class_group_id=class_group_id, teaches=teaches)
        self._authorize_or_raise(principal, action, resource, ctx, purpose=purpose)

        # deterministic: latest status per topic
        stmt = select(TopicState).where(TopicState.student_user_id == student_user_id, TopicState.school_id == school_id).order_by(TopicState.topic_id.asc(), TopicState.valid_from.desc(), TopicState.version.desc())
        rows = list(self.db.execute(stmt).scalars().all())
        latest_by_topic: dict[uuid.UUID, TopicState] = {}
        for r in rows:
            if r.topic_id not in latest_by_topic:
                latest_by_topic[r.topic_id] = r

        suggestions: list[dict[str, Any]] = []
        for topic_id, st in latest_by_topic.items():
            if st.status == TopicProgressStatus.VERIFIED_MASTERY.value:
                continue  # nothing to recommend
            if st.status == TopicProgressStatus.IN_PROGRESS_PRACTICE.value:
                reason = f"Deterministic: tema ma stav {st.status} na zaklade dokladu {st.evidence_attempt_ref or 'bez odkazu'}; odporuca sa pokracovat v precvicovani."
            else:  # PARTIALLY_MASTERED
                reason = f"Deterministic: tema ma stav {st.status} (ciastocne zvladnute) na zaklade dokladu {st.evidence_attempt_ref or 'bez odkazu'}; odporuca sa cielene precvicovanie pred overenim."
            suggestions.append({"topic_id": str(topic_id), "reason": reason, "suggested_action": "practice"})
            if persist:
                self.repo.add_recommendation(
                    school_id=school_id, student_user_id=student_user_id, topic_id=topic_id,
                    reason=reason, suggested_action="practice", is_demo=is_demo
                )
        audit_write(self.db, principal, action, resource, purpose, "success", {"count": len(suggestions), "persisted": persist})
        return suggestions
