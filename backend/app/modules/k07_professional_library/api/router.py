from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k07_professional_library.services.service import K07Service
from app.shared.types import Principal

router = APIRouter(prefix="/k07", tags=["k07"])


class ItemCreate(BaseModel):
    school_id: uuid.UUID | None = None
    owner_teacher_user_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    is_demo: bool = False


class VersionCreate(BaseModel):
    version_number: int
    content_text: str | None = None
    note: str | None = None
    is_demo: bool = False


class TagCreate(BaseModel):
    tag: str
    is_demo: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k07", "status": "ready"}


@router.post("/items")
def create_item(payload: ItemCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = payload.school_id or principal.school_id
    owner = payload.owner_teacher_user_id or principal.user_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    obj = K07Service(db).create_item(
        principal, school_id=school_id, owner_teacher_user_id=owner,
        title=payload.title, description=payload.description, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/items")
def list_items(
    owner_teacher_user_id: uuid.UUID | None = None,
    include_archived: bool = True,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    owner = owner_teacher_user_id or principal.user_id
    rows = K07Service(db).list_items(
        principal, school_id=school_id, owner_teacher_user_id=owner, include_archived=include_archived,
    )
    db.commit()
    return paginated(rows, page)


@router.post("/items/{item_id}/versions")
def add_version(item_id: uuid.UUID, payload: VersionCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K07Service(db).add_version(
        principal, item_id, version_number=payload.version_number,
        content_text=payload.content_text, note=payload.note, is_demo=payload.is_demo,
    )
    db.commit()
    return serialize(obj)


@router.get("/items/{item_id}/versions")
def list_versions(
    item_id: uuid.UUID,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = K07Service(db).list_versions(principal, item_id)
    db.commit()
    return paginated(rows, page)


@router.post("/items/{item_id}/tags")
def add_tag(item_id: uuid.UUID, payload: TagCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K07Service(db).add_tag(principal, item_id, payload.tag, is_demo=payload.is_demo)
    db.commit()
    return serialize(obj)


@router.post("/items/{item_id}/archive")
def archive_item(item_id: uuid.UUID, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    obj = K07Service(db).archive_item(principal, item_id)
    db.commit()
    return serialize(obj)
