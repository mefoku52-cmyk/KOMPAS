from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k12_analytics_center.services.service import K12Service
from app.shared.types import Principal

router = APIRouter(prefix="/analytics", tags=["k12-analytics"])


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k12", "status": "ready"}


@router.get("/overview")
def overview(
    school_id: uuid.UUID | None = None,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    target = school_id or principal.school_id
    if target is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    payload = K12Service(db).get_school_overview(principal, school_id=target)
    db.commit()
    return payload


@router.get("/students/{student_user_id}")
def individual_progress(
    student_user_id: uuid.UUID,
    purpose: str | None = None,
    school_id: uuid.UUID | None = None,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    target = school_id or principal.school_id
    if target is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    if not purpose:
        raise HTTPException(status_code=400, detail="purpose_required")
    payload = K12Service(db).get_individual_progress(
        principal, school_id=target, student_user_id=student_user_id, purpose=purpose,
    )
    db.commit()
    return payload
