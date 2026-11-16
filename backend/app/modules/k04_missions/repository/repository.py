from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k04_missions.domain.models import Mission, MissionAttempt, MissionTask


class K04Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_mission(self, *, school_id: uuid.UUID, topic_id: uuid.UUID, title: str, is_verification: bool = False, is_demo: bool = False) -> Mission:
        obj = Mission(school_id=school_id, topic_id=topic_id, title=title, is_verification=is_verification, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def create_task(self, *, school_id: uuid.UUID, mission_id: uuid.UUID, task_type: str, prompt: str, expected_answer: str, order_index: int = 0, is_demo: bool = False) -> MissionTask:
        obj = MissionTask(school_id=school_id, mission_id=mission_id, task_type=task_type, prompt=prompt, expected_answer=expected_answer, order_index=order_index, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_task(self, task_id: uuid.UUID) -> MissionTask | None:
        return self.db.get(MissionTask, task_id)

    def get_mission(self, mission_id: uuid.UUID) -> Mission | None:
        return self.db.get(Mission, mission_id)

    def list_tasks(self, mission_id: uuid.UUID) -> list[MissionTask]:
        stmt = select(MissionTask).where(MissionTask.mission_id == mission_id).order_by(MissionTask.order_index.asc(), MissionTask.id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def create_attempt(self, *, school_id: uuid.UUID, task_id: uuid.UUID, student_user_id: uuid.UUID, answer: str, is_correct: bool, is_demo: bool = False) -> MissionAttempt:
        obj = MissionAttempt(school_id=school_id, task_id=task_id, student_user_id=student_user_id, answer=answer, is_correct=is_correct, evaluated=True, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj
