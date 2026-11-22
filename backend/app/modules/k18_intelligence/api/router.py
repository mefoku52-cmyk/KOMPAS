from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.shared.types import Principal
from app.modules.k18_intelligence.services.orchestrator import IntelligenceOrchestrator
from app.modules.k18_intelligence.repository.store import ILStore, _to_dict

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class EventIn(BaseModel):
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = "api"
    school_id: Optional[str] = None
    correlation_id: Optional[str] = None
    event_id: Optional[str] = None
    locale: str = "sk"


class DismissIn(BaseModel):
    reason: str
    note: Optional[str] = None


class ApproveIn(BaseModel):
    approved: bool
    note: Optional[str] = None


@router.get("/status")
def status():
    return {"module": "intelligence", "status": "ready", "version": "v1"}


@router.post("/events")
def ingest_event(body: EventIn, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    orch = IntelligenceOrchestrator(db)
    import uuid as _uuid
    eid = _uuid.UUID(body.event_id) if body.event_id else None
    res = orch.process_event(body.event_type, body.payload, source=body.source, school_id=principal.school_id, event_id=eid, locale=body.locale)
    db.commit()
    return res


@router.get("/situations")
def situations(entity_id: Optional[str] = None, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    store = ILStore(db)
    inits = store.list_initiatives(entity_id=entity_id)
    by_entity = {}
    for i in inits:
        by_entity.setdefault(i.entity_id, []).append(i)
    items = []
    for eid, arr in by_entity.items():
        latest = arr[0]
        items.append({"id": str(latest.id), "entity_type": latest.entity_type, "entity_id": eid, "situation_type": latest.action_type, "severity": latest.urgency, "status": latest.status, "decision": latest.decision, "reason": latest.reason, "created_at": latest.created_at.isoformat()})
    return {"items": items}


@router.get("/situations/{entity_id}")
def situation_detail(entity_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    store = ILStore(db)
    inits = store.list_initiatives(entity_id=entity_id)
    init_ids = {str(i.id) for i in inits}
    comms = [c for c in store.list_communications() if c.get("entity_id") == entity_id]
    outs = [o for o in store.list_outcomes() if str(o.get("initiative_id")) in init_ids]
    return {
        "entity_id": entity_id,
        "hypotheses": [_to_dict(h) for h in store.list_hypotheses(entity_id=entity_id)],
        "predictions": [_to_dict(p) for p in store.list_predictions(entity_id=entity_id)],
        "initiatives": [_to_dict(i) for i in inits],
        "communications": comms,
        "outcomes": outs,
    }


@router.post("/situations/{initiative_id}/dismiss")
def dismiss(initiative_id: str, body: DismissIn, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    import uuid as _uuid
    try: iid = _uuid.UUID(initiative_id)
    except ValueError: raise HTTPException(400, "invalid initiative_id")
    store = ILStore(db)
    init = store.get_initiative(iid)
    if not init:
        raise HTTPException(404, "initiative not found")
    store.update_initiative_status(init.id, "dismissed", actor=str(principal.user_id))
    store.audit("situation.dismissed", {"reason": body.reason, "note": body.note}, actor=str(principal.user_id), entity_type="initiative", entity_id=str(init.id), school_id=principal.school_id)
    db.commit()
    return {"id": str(init.id), "status": "dismissed"}


@router.post("/situations/{initiative_id}/approve")
def approve(initiative_id: str, body: ApproveIn, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    import uuid as _uuid
    try: iid = _uuid.UUID(initiative_id)
    except ValueError: raise HTTPException(400, "invalid initiative_id")
    store = ILStore(db)
    init = store.get_initiative(iid)
    if not init:
        raise HTTPException(404, "initiative not found")
    status_val = "approved" if body.approved else "rejected"
    store.update_initiative_status(init.id, status_val, actor=str(principal.user_id))
    store.audit("initiative.approval", {"approved": body.approved, "note": body.note}, actor=str(principal.user_id), entity_type="initiative", entity_id=str(init.id), school_id=principal.school_id)
    db.commit()
    return {"id": str(init.id), "status": status_val}


@router.get("/notifications")
def notifications(role: Optional[str] = None, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    store = ILStore(db)
    return {"items": store.list_communications(recipient_role=role)}


@router.post("/notifications/{comm_id}/acknowledge")
def acknowledge(comm_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    import uuid as _uuid
    try: cid = _uuid.UUID(comm_id)
    except ValueError: raise HTTPException(400, "invalid communication_id")
    store = ILStore(db)
    comm = store.get_communication(cid)
    if not comm:
        raise HTTPException(404, "notification not found")
    store.ack_communication(comm.id)
    store.audit("notification.ack", {"communication_id": str(comm.id)}, actor=str(principal.user_id), entity_type="communication", entity_id=str(comm.id), school_id=principal.school_id)
    db.commit()
    return {"id": str(comm.id), "status": "acknowledged"}


@router.get("/audit")
def audit(limit: int = 200, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    store = ILStore(db)
    return {"items": store.list_audit(limit=limit)}
