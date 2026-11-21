from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k01_learning_profile.services.service import K01Service
from app.shared.types import Principal

router = APIRouter(prefix="/k01", tags=["k01"])


class ProfileCreate(BaseModel):
    school_id: uuid.UUID | None = None
    student_user_id: uuid.UUID
    school_year_id: uuid.UUID
    grade: int = Field(ge=1)
    label: str | None = None
    version: int = Field(default=1, ge=1)
    is_demo: bool = False
    purpose: str | None = None
    class_group_id: uuid.UUID | None = None
    teaches: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k01", "status": "ready"}


@router.post("/profiles")
def create_profile(payload: ProfileCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    service = K01Service(db)
    obj = service.create_profile(
        principal,
        school_id=school_id,
        student_user_id=payload.student_user_id,
        school_year_id=payload.school_year_id,
        grade=payload.grade,
        label=payload.label,
        version=payload.version,
        is_demo=payload.is_demo,
        purpose=payload.purpose,
        class_group_id=payload.class_group_id,
        teaches=payload.teaches,
    )
    db.commit()
    return serialize(obj)


@router.get("/profiles/{student_user_id}/history")
def list_history(
    student_user_id: uuid.UUID,
    purpose: str | None = None,
    class_group_id: uuid.UUID | None = None,
    teaches: bool = False,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K01Service(db).list_history(
        principal, student_user_id, school_id,
        purpose=purpose, class_group_id=class_group_id, teaches=teaches,
    )
    db.commit()
    return paginated(rows, page)


@router.get("/profiles/{student_user_id}/latest")
def get_latest(
    student_user_id: uuid.UUID,
    school_year_id: uuid.UUID | None = None,
    purpose: str | None = None,
    class_group_id: uuid.UUID | None = None,
    teaches: bool = False,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    row = K01Service(db).get_latest_for_year(
        principal, student_user_id, school_year_id, school_id,
        purpose=purpose, class_group_id=class_group_id, teaches=teaches,
    )
    db.commit()
    if row is None:
        raise HTTPException(status_code=404, detail="profile_not_found")
    return serialize(row)
