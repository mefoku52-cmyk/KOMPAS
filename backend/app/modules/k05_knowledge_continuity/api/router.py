from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k05_knowledge_continuity.services.service import K05Service
from app.shared.types import Principal

router = APIRouter(prefix="/k05", tags=["k05"])


class StateCreate(BaseModel):
    school_id: uuid.UUID | None = None
    student_user_id: uuid.UUID
    topic_id: uuid.UUID
    kind: str
    status: str
    evidence_attempt_ref: str | None = None
    is_verification_evidence: bool = False
    version: int = 1
    is_demo: bool = False
    purpose: str | None = None
    class_group_id: uuid.UUID | None = None
    teaches: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k05", "status": "ready"}


@router.post("/states")
def record_state(payload: StateCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K05Service(db).record_state(
        principal, school_id=school_id, student_user_id=payload.student_user_id,
        topic_id=payload.topic_id, kind=payload.kind, status=payload.status,
        evidence_attempt_ref=payload.evidence_attempt_ref,
        is_verification_evidence=payload.is_verification_evidence,
        version=payload.version, is_demo=payload.is_demo, purpose=payload.purpose,
        class_group_id=payload.class_group_id, teaches=payload.teaches,
    )
    db.commit()
    return serialize(obj)


@router.get("/states/{student_user_id}")
def list_states(
    student_user_id: uuid.UUID,
    topic_id: uuid.UUID | None = None,
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
    rows = K05Service(db).list_states(
        principal, student_user_id=student_user_id, school_id=school_id,
        topic_id=topic_id, purpose=purpose, class_group_id=class_group_id, teaches=teaches,
    )
    db.commit()
    return paginated(rows, page)
