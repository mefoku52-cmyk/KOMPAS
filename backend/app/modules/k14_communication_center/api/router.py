from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k14_communication_center.services.service import K14Service
from app.shared.types import Principal

router = APIRouter(prefix="/communication", tags=["k14-communication"])


class ThreadCreate(BaseModel):
    school_id: uuid.UUID | None = None
    subject: str
    participant_user_ids: list[uuid.UUID] = []
    is_private: bool = False
    is_demo: bool = False


class MessageCreate(BaseModel):
    body: str
    is_demo: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k14", "status": "ready"}


@router.post("/threads")
def create_thread(payload: ThreadCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K14Service(db).create_thread(
        principal, school_id=school_id, subject=payload.subject,
        participant_user_ids=payload.participant_user_ids,
        is_private=payload.is_private, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/threads")
def list_threads(
    school_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    target = school_id or principal.school_id
    if target is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K14Service(db).list_threads(principal, school_id=target)
    db.commit()
    return paginated(rows, page)


@router.post("/threads/{thread_id}/messages")
def post_message(thread_id: uuid.UUID, payload: MessageCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K14Service(db).post_message(principal, thread_id=thread_id, body=payload.body, is_demo=payload.is_demo)
    db.commit()
    return serialize(obj)


@router.get("/threads/{thread_id}/messages")
def list_messages(
    thread_id: uuid.UUID,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K14Service(db).list_messages(principal, thread_id=thread_id)
    db.commit()
    payload = paginated(rows, page)
    sender_ids = {row.sender_user_id for row in rows}
    if sender_ids:
        from sqlalchemy import select

        from app.shared.identity import User

        names = {
            str(uid): full_name
            for uid, full_name in db.execute(select(User.id, User.full_name).where(User.id.in_(sender_ids))).all()
        }
        for item in payload["items"]:
            item["sender_full_name"] = names.get(item.get("sender_user_id"))
    return payload
