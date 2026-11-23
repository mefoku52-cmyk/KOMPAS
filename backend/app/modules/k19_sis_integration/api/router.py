from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k19_sis_integration.services.sync_service import SISService
from app.shared.types import Principal

router = APIRouter(prefix="/integrations/sis", tags=["k19-sis"])


class SourceCreate(BaseModel):
    school_id: uuid.UUID | None = None
    provider_type: str = "edupage"
    name: str
    subdomain: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    config: dict = Field(default_factory=dict)
    is_enabled: bool = False


class SourceUpdate(BaseModel):
    name: str | None = None
    subdomain: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    config: dict | None = None
    is_enabled: bool | None = None


class SyncRun(BaseModel):
    mode: str = "full"


def _school(principal: Principal, school_id: uuid.UUID | None) -> uuid.UUID:
    target = school_id or principal.school_id
    if target is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    return target


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k19_sis_integration", "status": "ready"}


@router.get("/sources")
def list_sources(school_id: uuid.UUID | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, school_id)
    try:
        items = SISService(db).list_sources(principal, school_id=target)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    db.commit()
    return {"items": items, "total": len(items)}


@router.post("/sources")
def create_source(payload: SourceCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, payload.school_id)
    try:
        src = SISService(db).create_source(
            principal, school_id=target, provider_type=payload.provider_type, name=payload.name,
            subdomain=payload.subdomain, base_url=payload.base_url, api_key=payload.api_key,
            config=payload.config, is_enabled=payload.is_enabled,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return SISService(db)._source_public(src)


@router.patch("/sources/{source_id}")
def update_source(source_id: uuid.UUID, payload: SourceUpdate, school_id: uuid.UUID | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, school_id)
    try:
        src = SISService(db).update_source(
            principal, school_id=target, source_id=source_id, name=payload.name, subdomain=payload.subdomain,
            base_url=payload.base_url, api_key=payload.api_key, config=payload.config, is_enabled=payload.is_enabled,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return SISService(db)._source_public(src)


@router.post("/sources/{source_id}/test")
def test_source(source_id: uuid.UUID, school_id: uuid.UUID | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, school_id)
    try:
        result = SISService(db).test_connection(principal, school_id=target, source_id=source_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"connection_failed:{exc}")
    db.commit()
    return result


@router.post("/sources/{source_id}/sync")
def run_sync(source_id: uuid.UUID, payload: SyncRun, school_id: uuid.UUID | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, school_id)
    try:
        job = SISService(db).run_sync(principal, school_id=target, source_id=source_id, mode=payload.mode)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"sync_failed:{exc}")
    db.commit()
    return job


@router.get("/jobs")
def list_jobs(school_id: uuid.UUID | None = None, source_id: uuid.UUID | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, school_id)
    try:
        items = SISService(db).list_jobs(principal, school_id=target, source_id=source_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    db.commit()
    return {"items": items, "total": len(items)}


@router.get("/jobs/{job_id}")
def get_job(job_id: uuid.UUID, school_id: uuid.UUID | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, school_id)
    try:
        item = SISService(db).get_job(principal, school_id=target, job_id=job_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return item


@router.get("/conflicts")
def list_conflicts(school_id: uuid.UUID | None = None, source_id: uuid.UUID | None = None, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    target = _school(principal, school_id)
    try:
        items = SISService(db).list_conflicts(principal, school_id=target, source_id=source_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    db.commit()
    return {"items": items, "total": len(items)}
