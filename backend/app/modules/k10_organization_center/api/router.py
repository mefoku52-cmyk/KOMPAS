from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k10_organization_center.services.service import K10Service
from app.shared.types import Principal

router = APIRouter(prefix="/k10", tags=["k10"])


class TaskCreate(BaseModel):
    school_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    is_demo: bool = False


class PlanCreate(BaseModel):
    school_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    is_demo: bool = False


class AssignCreate(BaseModel):
    school_id: uuid.UUID | None = None
    assignee_user_id: uuid.UUID
    role_in_task: str | None = None
    is_demo: bool = False


def _school(principal: Principal, explicit: uuid.UUID | None) -> uuid.UUID:
    school_id = explicit or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    return school_id


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k10", "status": "ready"}


@router.post("/tasks")
def create_task(payload: TaskCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K10Service(db).create_task(
        principal, school_id=_school(principal, payload.school_id),
        title=payload.title, description=payload.description, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/tasks")
def list_tasks(
    school_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K10Service(db).list_tasks(principal, _school(principal, school_id))
    db.commit()
    return paginated(rows, page)


@router.post("/tasks/{task_id}/assignments")
def assign_task(task_id: uuid.UUID, payload: AssignCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K10Service(db).assign_task(
        principal, school_id=_school(principal, payload.school_id), task_id=task_id,
        assignee_user_id=payload.assignee_user_id, role_in_task=payload.role_in_task, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.post("/plans")
def create_plan(payload: PlanCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K10Service(db).create_plan(
        principal, school_id=_school(principal, payload.school_id),
        name=payload.name, description=payload.description, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/plans")
def list_plans(
    school_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K10Service(db).list_plans(principal, _school(principal, school_id))
    db.commit()
    return paginated(rows, page)
