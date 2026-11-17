from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k03_adaptive_learning.services.service import K03Service
from app.shared.types import Principal

router = APIRouter(prefix="/k03", tags=["k03"])


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k03", "status": "ready"}


@router.get("/recommendations/{student_user_id}")
def recommendations(
    student_user_id: uuid.UUID,
    purpose: str | None = None,
    class_group_id: uuid.UUID | None = None,
    teaches: bool = False,
    persist: bool = False,
    is_demo: bool = False,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K03Service(db).recommend_for_student(
        principal, school_id=school_id, student_user_id=student_user_id,
        purpose=purpose, class_group_id=class_group_id, teaches=teaches,
        persist=persist, is_demo=is_demo,
    )
    db.commit()
    return paginated(rows, page)
