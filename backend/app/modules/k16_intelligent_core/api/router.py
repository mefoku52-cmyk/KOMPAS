from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.permissions.policy import Scope
from app.core.security.auth import get_current_principal
from app.modules.k16_intelligent_core.services.service import K16ServiceFacade
from app.shared.types import Principal

router = APIRouter(prefix="/k16", tags=["k16"])


class SourceCreate(BaseModel):
    school_id: uuid.UUID | None = None
    name: str
    source_type: str
    content: str
    approved: bool = False


class ContextMemoryCreate(BaseModel):
    school_id: uuid.UUID | None = None
    source_record_ref: str
    content: str


class OrchestratorRun(BaseModel):
    school_id: uuid.UUID | None = None
    task: str
    prompt: str
    payload: dict[str, Any] = Field(default_factory=dict)


def _school(principal: Principal, explicit: uuid.UUID | None) -> uuid.UUID:
    school_id = explicit or principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    return school_id


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k16", "status": "ready"}


@router.post("/sources")
def register_source(payload: SourceCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    facade = K16ServiceFacade(db)
    obj = facade.knowledge.register_source(
        principal, _school(principal, payload.school_id), payload.name,
        payload.source_type, payload.content, approved=payload.approved,
    )
    db.commit()
    return serialize(obj)


@router.get("/knowledge")
def search_knowledge(
    q: str,
    school_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    facade = K16ServiceFacade(db)
    rows = facade.knowledge.search_approved(principal, _school(principal, school_id), q)
    db.commit()
    return paginated(rows, page)


@router.post("/context-memory")
def add_context_memory(payload: ContextMemoryCreate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    facade = K16ServiceFacade(db)
    obj = facade.context_memory.add_record(
        principal, _school(principal, payload.school_id), payload.source_record_ref, payload.content,
    )
    db.commit()
    return serialize(obj)


@router.get("/context-memory")
def list_context_memory(
    school_id: uuid.UUID | None = None,
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    facade = K16ServiceFacade(db)
    rows = facade.context_memory.list_records(principal, _school(principal, school_id))
    db.commit()
    return paginated(rows, page)


@router.post("/orchestrator/run")
def run_orchestrator(payload: OrchestratorRun, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = _school(principal, payload.school_id)
    facade = K16ServiceFacade(db)
    output = facade.orchestrator.run(
        principal,
        task=payload.task,
        prompt=payload.prompt,
        payload=payload.payload,
        context={"school_id": school_id, "scope": Scope.SCHOOL_AGGREGATE.value},
    )
    db.commit()
    return {"output": output, "provider": "null", "external_calls": False}


@router.get("/audit/report")
def audit_report(
    school_id: uuid.UUID | None = None,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    facade = K16ServiceFacade(db)
    payload = facade.audit_engine.report(principal, school_id=_school(principal, school_id))
    db.commit()
    return payload
