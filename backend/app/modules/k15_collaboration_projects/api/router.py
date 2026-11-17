from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k15_collaboration_projects.services.service import K15Service
from app.shared.types import Principal

router = APIRouter(prefix="/projects", tags=["k15-projects"])


class ProjectCreate(BaseModel):
    school_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    member_user_ids: list[uuid.UUID] | None = None
    is_demo: bool = False


class MemberCreate(BaseModel):
    user_id: uuid.UUID
    role: str = "member"
    is_demo: bool = False


class ProjectTaskCreate(BaseModel):
    title: str
    description: str | None = None
    assignee_user_id: uuid.UUID | None = None
    is_demo: bool = False


class SubmissionCreate(BaseModel):
    content: str
    is_demo: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k15", "status": "ready"}


@router.post("")
def create_project(payload: ProjectCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K15Service(db).create_project(
        principal, school_id=school_id, title=payload.title,
        description=payload.description, member_user_ids=payload.member_user_ids, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/{project_id}")
def get_project(project_id: uuid.UUID, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K15Service(db).get_project(principal, project_id=project_id)
    db.commit()
    return serialize(obj)


@router.post("/{project_id}/members")
def add_member(project_id: uuid.UUID, payload: MemberCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K15Service(db).add_member(
        principal, project_id=project_id, user_id=payload.user_id,
        role=payload.role, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.post("/{project_id}/tasks")
def create_task(project_id: uuid.UUID, payload: ProjectTaskCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K15Service(db).create_task(
        principal, project_id=project_id, title=payload.title,
        description=payload.description, assignee_user_id=payload.assignee_user_id, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/{project_id}/tasks")
def list_tasks(
    project_id: uuid.UUID,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K15Service(db).list_tasks(principal, project_id=project_id)
    db.commit()
    return paginated(rows, page)


@router.post("/tasks/{task_id}/submissions")
def submit(task_id: uuid.UUID, payload: SubmissionCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K15Service(db).submit(principal, task_id=task_id, content=payload.content, is_demo=payload.is_demo)
    db.commit()
    return serialize(obj)


@router.get("/tasks/{task_id}/submissions")
def list_submissions(
    task_id: uuid.UUID,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K15Service(db).list_submissions(principal, task_id=task_id)
    db.commit()
    return paginated(rows, page)
