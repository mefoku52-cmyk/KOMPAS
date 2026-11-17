from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k13_parent_center.services.service import K13Service
from app.shared.types import Principal

router = APIRouter(prefix="/parent", tags=["k13-parent"])


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k13", "status": "ready"}


@router.get("/children")
def list_children(
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    payload = K13Service(db).list_children(principal, school_id=school_id)
    db.commit()
    children = [uuid.UUID(value) for value in payload.get("child_user_ids", [])]
    return paginated(children, page)


@router.get("/children/{child_user_id}")
def child_overview(
    child_user_id: uuid.UUID,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    payload = K13Service(db).get_child_overview(principal, school_id=school_id, child_user_id=child_user_id)
    db.commit()
    return payload
