from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k05_knowledge_continuity.domain.models import TopicProgressKind, TopicProgressStatus
from app.modules.k05_knowledge_continuity.repository.repository import K05Repository
from app.shared.types import Principal, Role


class K05Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K05Repository(db)

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

    def record_state(
        self,
        principal: Principal,
        *,
        school_id: uuid.UUID,
        student_user_id: uuid.UUID,
        topic_id: uuid.UUID,
        kind: TopicProgressKind | str,
        status: TopicProgressStatus | str,
        evidence_attempt_ref: str | None = None,
        is_verification_evidence: bool = False,
        version: int = 1,
        is_demo: bool = False,
        purpose: str | None = None,
        class_group_id: uuid.UUID | None = None,
        teaches: bool = False,
    ):
        action = "k05.record_state"
        resource = f"progress_topic_state:student:{student_user_id}:topic:{topic_id}"
        kind_val = TopicProgressKind(kind).value if not isinstance(kind, TopicProgressKind) else kind.value
        status_val = TopicProgressStatus(status).value if not isinstance(status, TopicProgressStatus) else status.value

        # rules
        if status_val == TopicProgressStatus.VERIFIED_MASTERY.value:
            if kind_val != TopicProgressKind.VERIFIED.value:
                raise ValueError("verified_mastery_requires_verified_kind")
            if not is_verification_evidence or not evidence_attempt_ref:
                raise ValueError("verified_mastery_requires_verification_evidence")
        if kind_val == TopicProgressKind.VERIFIED.value and not is_verification_evidence:
            raise ValueError("verified_kind_requires_verification_evidence")

        if principal.is_system:
            ctx = {"school_id": school_id, "system_internal": True}
        elif principal.role == Role.TEACHER:
            ctx = {"scope": Scope.TEACHES_CLASS.value, "student_user_id": student_user_id, "class_group_id": class_group_id, "teacher_user_id": principal.user_id if teaches else None, "teaches": teaches, "school_id": school_id}
        elif principal.role == Role.LEADERSHIP:
            ctx = {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": school_id, "student_user_id": student_user_id, "purpose": purpose}
        elif principal.user_id == student_user_id and kind_val == TopicProgressKind.PRACTICED.value and status_val == TopicProgressStatus.IN_PROGRESS_PRACTICE.value:
            # allow student to record own practice progress only (not verified mastery)
            ctx = {"scope": Scope.SELF.value, "owner_user_id": student_user_id, "student_user_id": student_user_id, "school_id": school_id}
        else:
            ctx = {"school_id": school_id}

        self._authorize_or_raise(principal, action, resource, ctx, purpose=purpose)
        obj = self.repo.create_state(
            school_id=school_id,
            student_user_id=student_user_id,
            topic_id=topic_id,
            kind=kind_val,
            status=status_val,
            evidence_attempt_ref=evidence_attempt_ref,
            is_verification_evidence=is_verification_evidence,
            version=version,
            is_demo=is_demo,
        )
        audit_write(self.db, principal, action, resource, purpose, "success", {"state_id": str(obj.id), "kind": kind_val, "status": status_val})
        return obj

    def list_states(self, principal: Principal, *, student_user_id: uuid.UUID, school_id: uuid.UUID, topic_id: uuid.UUID | None = None, purpose: str | None = None, class_group_id: uuid.UUID | None = None, teaches: bool = False):
        action = "k05.list_states"
        resource = f"progress_topic_state:student:{student_user_id}"
        ctx = self._view_context(principal, student_user_id=student_user_id, school_id=school_id, purpose=purpose, class_group_id=class_group_id, teaches=teaches)
        self._authorize_or_raise(principal, action, resource, ctx, purpose=purpose)
        rows = self.repo.list_states(student_user_id, topic_id=topic_id, school_id=school_id)
        audit_write(self.db, principal, action, resource, purpose, "success", {"count": len(rows)})
        return rows
