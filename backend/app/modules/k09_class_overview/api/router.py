from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k09_class_overview.services.service import K09Service
from app.shared.types import Principal

router = APIRouter(prefix="/k09", tags=["k09"])


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k09", "status": "ready"}


@router.get("/classes")
def list_classes(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    try:
        items = K09Service(db).list_my_classes(principal, school_id=school_id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="forbidden")
    db.commit()
    return {"items": items, "total": len(items)}


@router.get("/classes/{class_group_id}/overview")
def class_overview(
    class_group_id: uuid.UUID,
    topic_id: uuid.UUID | None = None,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    payload = K09Service(db).get_class_overview(
        principal, school_id=school_id, class_group_id=class_group_id, topic_id=topic_id,
    )
    db.commit()
    return payload
