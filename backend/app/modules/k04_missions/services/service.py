from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.events.bus import DomainEvent, EventBus, bus as default_bus
from app.core.permissions.policy import Scope, authorize
from app.modules.k04_missions.domain.models import TaskType
from app.modules.k04_missions.repository.repository import K04Repository
from app.shared.types import Principal, Role


def evaluate_answer(task_type: str | TaskType, expected: str, answer: str) -> bool:
    t = TaskType(task_type).value if not isinstance(task_type, TaskType) else task_type.value
    if t == TaskType.CHOICE.value:
        return str(answer).strip().lower() == str(expected).strip().lower()
    if t == TaskType.NUMERIC.value:
        try:
            return float(str(answer).strip()) == float(str(expected).strip())
        except (TypeError, ValueError):
            return False
    if t == TaskType.TEXT_MATCH.value:
        return str(answer).strip().casefold() == str(expected).strip().casefold()
    return False


class K04Service:
    def __init__(self, db: Session, event_bus: EventBus | None = None):
        self.db = db
        self.repo = K04Repository(db)
        self.bus = event_bus or default_bus

    def _authorize_or_raise(self, principal: Principal, action: str, resource: str, context: dict, purpose: str | None = None):
        decision = authorize(principal, action, resource, context=context, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, purpose, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def create_mission(self, principal: Principal, *, school_id: uuid.UUID, topic_id: uuid.UUID, title: str, is_verification: bool = False, is_demo: bool = False):
        action = "k04.create_mission"
        resource = f"learning_mission:topic:{topic_id}"
        purpose = "manage_learning_content"
        if principal.is_system:
            ctx = {"school_id": school_id, "system_internal": True}
            used_purpose = None
        elif principal.role == Role.LEADERSHIP:
            ctx = {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": school_id, "purpose": purpose}
            used_purpose = purpose
        else:
            ctx = {"school_id": school_id}
            used_purpose = None
        self._authorize_or_raise(principal, action, resource, ctx, purpose=used_purpose)
        obj = self.repo.create_mission(school_id=school_id, topic_id=topic_id, title=title, is_verification=is_verification, is_demo=is_demo)
        audit_write(self.db, principal, action, f"learning_mission:{obj.id}", used_purpose, "success")
        return obj

    def submit_attempt(self, principal: Principal, *, task_id: uuid.UUID, student_user_id: uuid.UUID, answer: str, is_demo: bool = False):
        action = "k04.submit_attempt"
        task = self.repo.get_task(task_id)
        if not task:
            raise ValueError("task_not_found")
        mission = self.repo.get_mission(task.mission_id)
        if not mission:
            raise ValueError("mission_not_found")
        resource = f"learning_task:{task_id}"
        if principal.is_system:
            ctx = {"school_id": task.school_id, "system_internal": True}
        elif principal.user_id == student_user_id and principal.role == Role.STUDENT:
            ctx = {"scope": Scope.SELF.value, "owner_user_id": student_user_id, "student_user_id": student_user_id, "school_id": task.school_id}
        else:
            ctx = {"school_id": task.school_id}
        self._authorize_or_raise(principal, action, resource, ctx)
        correct = evaluate_answer(task.task_type, task.expected_answer, answer)
        attempt = self.repo.create_attempt(school_id=task.school_id, task_id=task_id, student_user_id=student_user_id, answer=answer, is_correct=correct, is_demo=is_demo)
        audit_write(self.db, principal, action, f"learning_attempt:{attempt.id}", None, "success", {"correct": correct})
        event = DomainEvent(
            event_type="AnswerEvaluated",
            school_id=task.school_id,
            payload={
                "school_id": str(task.school_id),
                "student_user_id": student_user_id,
                "topic_id": mission.topic_id,
                "attempt_ref": str(attempt.id),
                "is_verification": bool(mission.is_verification),
                "correct": bool(correct),
            },
        )
        self.bus.publish(event, db=self.db)
        return attempt
