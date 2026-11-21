from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k04_missions.services.service import K04Service
from app.shared.types import Principal

router = APIRouter(prefix="/k04", tags=["k04"])


class MissionCreate(BaseModel):
    school_id: uuid.UUID | None = None
    topic_id: uuid.UUID
    title: str
    is_verification: bool = False
    is_demo: bool = False


class TaskCreate(BaseModel):
    task_type: str
    prompt: str
    expected_answer: str
    order_index: int = 0
    is_demo: bool = False


class AttemptCreate(BaseModel):
    task_id: uuid.UUID
    student_user_id: uuid.UUID | None = None
    answer: str
    is_demo: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k04", "status": "ready"}


@router.get("/missions")
def list_missions(
    school_id: uuid.UUID | None = None,
    topic_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    target = school_id or principal.school_id
    if target is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K04Service(db).list_missions(principal, school_id=target, topic_id=topic_id)
    db.commit()
    return paginated(rows, page)


@router.post("/missions")
def create_mission(payload: MissionCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K04Service(db).create_mission(
        principal, school_id=school_id, topic_id=payload.topic_id,
        title=payload.title, is_verification=payload.is_verification, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.post("/missions/{mission_id}/tasks")
def create_task(mission_id: uuid.UUID, payload: TaskCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K04Service(db).create_task(
        principal, mission_id=mission_id, task_type=payload.task_type,
        prompt=payload.prompt, expected_answer=payload.expected_answer,
        order_index=payload.order_index, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/missions/{mission_id}/tasks")
def list_tasks(
    mission_id: uuid.UUID,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K04Service(db).list_tasks(principal, mission_id)
    db.commit()
    return paginated(rows, page)


@router.get("/attempts/mine")
def list_my_attempts(
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K04Service(db).list_my_attempts(principal)
    db.commit()
    return paginated(rows, page)


@router.post("/attempts")
def submit_attempt(payload: AttemptCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    student_user_id = payload.student_user_id or principal.user_id
    obj = K04Service(db).submit_attempt(
        principal, task_id=payload.task_id, student_user_id=student_user_id,
        answer=payload.answer, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)
