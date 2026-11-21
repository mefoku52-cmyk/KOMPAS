from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.api import serialize
from app.core.events.bus import DomainEvent, EventBus, bus as default_bus
from app.core.permissions.policy import Scope, authorize
from app.modules.k04_missions.domain.models import TaskType
from app.modules.k04_missions.repository.repository import K04Repository
from app.shared.types import Principal, Role


def _normalise_number(value: str) -> str:
    """'0,75' -> '0.75' — pupils write the decimal comma, never the dot."""
    return str(value).strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")


def evaluate_answer(task_type: str | TaskType, expected: str, answer: str) -> bool:
    t = TaskType(task_type).value if not isinstance(task_type, TaskType) else task_type.value
    if t == TaskType.CHOICE.value:
        return str(answer).strip().lower() == str(expected).strip().lower()
    if t == TaskType.NUMERIC.value:
        raw_answer, raw_expected = _normalise_number(answer), _normalise_number(expected)
        try:
            return float(raw_answer) == float(raw_expected)
        except (TypeError, ValueError):
            # fractions and other non-float numerics compare as text
            return raw_answer.casefold() == raw_expected.casefold()
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

    def create_task(self, principal: Principal, *, mission_id: uuid.UUID, task_type: str, prompt: str, expected_answer: str, order_index: int = 0, is_demo: bool = False):
        action = "k04.create_task"
        mission = self.repo.get_mission(mission_id)
        if not mission:
            raise ValueError("mission_not_found")
        if principal.is_system:
            ctx = {"school_id": mission.school_id, "system_internal": True}
        elif principal.role == Role.LEADERSHIP:
            purpose = "manage_learning_content"
            ctx = {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": mission.school_id, "purpose": purpose}
        else:
            ctx = {"school_id": mission.school_id}
        self._authorize_or_raise(principal, action, f"learning_mission:{mission_id}", ctx)
        obj = self.repo.create_task(school_id=mission.school_id, mission_id=mission_id, task_type=task_type, prompt=prompt, expected_answer=expected_answer, order_index=order_index, is_demo=is_demo)
        audit_write(self.db, principal, action, f"learning_task:{obj.id}", None, "success")
        return obj

    def list_tasks(self, principal: Principal, mission_id: uuid.UUID):
        action = "k04.list_tasks"
        mission = self.repo.get_mission(mission_id)
        if not mission:
            raise ValueError("mission_not_found")
        if principal.is_system:
            ctx = {"school_id": mission.school_id, "system_internal": True}
        elif principal.role == Role.TEACHER:
            ctx = {"scope": Scope.TEACHES_CLASS.value, "school_id": mission.school_id, "student_user_id": None, "class_group_id": None, "teacher_user_id": principal.user_id, "teaches": True}
        elif principal.role == Role.LEADERSHIP:
            ctx = {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE.value, "school_id": mission.school_id, "purpose": "manage_learning_content"}
        elif principal.role == Role.STUDENT and principal.school_id == mission.school_id:
            rows = self.repo.list_tasks(mission_id)
            audit_write(self.db, principal, action, f"learning_mission:{mission_id}", None, "success", {"count": len(rows)})
            return rows
        else:
            ctx = {"school_id": mission.school_id}
        self._authorize_or_raise(principal, action, f"learning_mission:{mission_id}", ctx)
        rows = self.repo.list_tasks(mission_id)
        audit_write(self.db, principal, action, f"learning_mission:{mission_id}", None, "success", {"count": len(rows)})
        return rows

    def list_missions(self, principal: Principal, *, school_id: uuid.UUID, topic_id: uuid.UUID | None = None):
        """Missions of a school. Visible to everyone who belongs to that school."""
        action = "k04.list_missions"
        if not (principal.is_system or principal.school_id == school_id):
            audit_write(self.db, principal, action, f"school:{school_id}", None, "denied", {"reason": "school_scope_denied"})
            raise PermissionError("school_scope_denied")
        rows = self.repo.list_missions(school_id, topic_id=topic_id)
        audit_write(self.db, principal, action, f"school:{school_id}", None, "success", {"count": len(rows)})
        return rows

    def list_my_attempts(self, principal: Principal):
        """The authenticated student's own submissions (answers + correctness)."""
        action = "k04.list_my_attempts"
        if principal.role != Role.STUDENT or principal.school_id is None:
            audit_write(self.db, principal, action, f"student:{principal.user_id}", None, "denied", {"reason": "student_only"})
            raise PermissionError("student_only")
        rows = self.repo.list_student_attempts(principal.school_id, principal.user_id)
        prompts = self.repo.task_prompts([row.task_id for row in rows])
        result = []
        for row in rows:
            payload = serialize(row)
            payload["task_prompt"] = prompts.get(row.task_id)
            result.append(payload)
        audit_write(self.db, principal, action, f"student:{principal.user_id}", None, "success", {"count": len(result)})
        return result
