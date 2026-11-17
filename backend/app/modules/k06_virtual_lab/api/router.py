from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.api import Page, page_params, paginated, serialize
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.modules.k06_virtual_lab.services.service import K06Service
from app.shared.types import Principal

router = APIRouter(prefix="/lab", tags=["k06-virtual-lab"])


class SimulationRun(BaseModel):
    definition_id: uuid.UUID
    inputs: dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = False


@router.get("/status")
def status(principal: Principal = Depends(get_current_principal)):
    return {"module": "k06", "status": "ready"}


@router.get("/definitions")
def list_definitions(
    page: Page = Depends(page_params),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    rows = K06Service(db).list_definitions(principal, school_id=school_id)
    db.commit()
    return paginated(rows, page)


@router.post("/simulations")
def run_simulation(payload: SimulationRun, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    school_id = principal.school_id
    if school_id is None:
        raise HTTPException(status_code=400, detail="school_id_required")
    run, outputs = K06Service(db).run_simulation(
        principal, school_id=school_id, definition_id=payload.definition_id,
        inputs=payload.inputs, is_demo=payload.is_demo,
    )
    db.commit()
    return {"run": serialize(run), "outputs": outputs}
