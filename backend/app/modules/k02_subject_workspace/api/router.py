from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k02_subject_workspace.services.service import K02Service
from app.shared.types import Principal

router = APIRouter(prefix="/k02", tags=["k02"])


class WorkspaceCreate(BaseModel):
    school_id: uuid.UUID | None = None
    subject_id: uuid.UUID
    teacher_user_id: uuid.UUID
    name: str
    is_demo: bool = False


class NodeCreate(BaseModel):
    title: str
    topic_id: uuid.UUID | None = None
    parent_node_id: uuid.UUID | None = None
    order_index: int = 0
    is_demo: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k02", "status": "ready"}


@router.post("/workspaces")
def create_workspace(payload: WorkspaceCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K02Service(db).create_workspace(
        principal, school_id=school_id, subject_id=payload.subject_id,
        teacher_user_id=payload.teacher_user_id, name=payload.name, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/workspaces")
def list_workspaces(
    teacher_user_id: uuid.UUID,
    purpose: str | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K02Service(db).list_workspaces(principal, teacher_user_id, school_id, purpose=purpose)
    db.commit()
    return paginated(rows, page)


@router.get("/workspaces/{workspace_id}")
def get_workspace(workspace_id: uuid.UUID, purpose: str | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K02Service(db).get_workspace(principal, workspace_id, purpose=purpose)
    db.commit()
    return serialize(obj)


@router.post("/workspaces/{workspace_id}/nodes")
def add_node(workspace_id: uuid.UUID, payload: NodeCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K02Service(db).add_node(
        principal, workspace_id, title=payload.title, topic_id=payload.topic_id,
        parent_node_id=payload.parent_node_id, order_index=payload.order_index, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/workspaces/{workspace_id}/nodes")
def list_nodes(
    workspace_id: uuid.UUID,
    purpose: str | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K02Service(db).list_nodes(principal, workspace_id, purpose=purpose)
    db.commit()
    return paginated(rows, page)
