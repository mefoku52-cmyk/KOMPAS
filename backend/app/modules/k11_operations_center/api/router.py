from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k11_operations_center.services.service import K11Service
from app.shared.types import Principal

router = APIRouter(prefix="/k11", tags=["k11"])


class RequestCreate(BaseModel):
    school_id: uuid.UUID | None = None
    request_type: str
    title: str
    description: str | None = None
    is_demo: bool = False


class TransitionCreate(BaseModel):
    new_status: str


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k11", "status": "ready"}


@router.post("/requests")
def create_request(payload: RequestCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K11Service(db).create_request(
        principal, school_id=school_id, request_type=payload.request_type,
        title=payload.title, description=payload.description, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/requests")
def list_requests(
    school_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    target = school_id or principal.school_id
    if target is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K11Service(db).list_requests(principal, target)
    db.commit()
    return paginated(rows, page)


@router.post("/requests/{request_id}/transition")
def transition(request_id: uuid.UUID, payload: TransitionCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K11Service(db).transition(principal, request_id, payload.new_status)
    db.commit()
    return serialize(obj)
