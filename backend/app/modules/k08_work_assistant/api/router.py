from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k08_work_assistant.services.service import K08Service
from app.shared.types import Principal

router = APIRouter(prefix="/k08", tags=["k08"])


class DraftCreate(BaseModel):
    school_id: uuid.UUID | None = None
    teacher_user_id: uuid.UUID | None = None
    title: str
    draft_type: str
    topics: list[str] | None = None
    use_orchestrator: bool = False
    is_demo: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k08", "status": "ready"}


@router.post("/drafts")
def create_draft(payload: DraftCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    teacher = payload.teacher_user_id or principal.user_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K08Service(db).generate_draft(
        principal, school_id=school_id, teacher_user_id=teacher,
        title=payload.title, draft_type=payload.draft_type, topics=payload.topics,
        use_orchestrator=payload.use_orchestrator, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/drafts")
def list_drafts(
    teacher_user_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K08Service(db).list_drafts(principal, school_id=school_id, teacher_user_id=teacher_user_id or principal.user_id)
    db.commit()
    return paginated(rows, page)


@router.post("/drafts/{draft_id}/submit")
def submit_draft(draft_id: uuid.UUID, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K08Service(db).submit_for_approval(principal, draft_id)
    db.commit()
    return serialize(obj)


@router.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: uuid.UUID, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K08Service(db).approve(principal, draft_id)
    db.commit()
    return serialize(obj)
