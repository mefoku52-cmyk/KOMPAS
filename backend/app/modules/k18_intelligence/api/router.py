from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.shared.types import Principal, Role
from app.modules.k18_intelligence.services.orchestrator import IntelligenceOrchestrator
from app.modules.k18_intelligence.repository.store import ILStore, _to_dict
from app.modules.k18_intelligence.repository.models import ILInitiative, ILCommunication, ILHypothesis, ILPrediction, ILOutcome, ILPerceptionEvent, ILAudit, ILDeadLetter
from app.modules.k18_intelligence.config import SETTINGS as K18_SETTINGS
from app.modules.k18_intelligence.api._auth import require

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
    require(principal, "intelligence.ingest", "intelligence", context={"allow_authenticated_school": True, "school_id": principal.school_id}, db=db)
    orch = IntelligenceOrchestrator(db)
    import uuid as _uuid
    eid = _uuid.UUID(body.event_id) if body.event_id else None
    school_id = body.school_id or (str(principal.school_id) if principal.school_id else None)
    res = orch.process_event(body.event_type, body.payload, source=body.source, school_id=school_id, event_id=eid, locale=body.locale)
    db.commit()
    return res


@router.get("/situations")
def situations(entity_id: Optional[str] = None, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    require(principal, "intelligence.read", "intelligence", context={"allow_authenticated_school": True, "school_id": principal.school_id}, db=db)
    store = ILStore(db)
    q = select(ILInitiative)
    if entity_id:
        q = q.where(ILInitiative.entity_id == entity_id)
    if principal.role in (Role.STUDENT, Role.PARENT):
        q = q.where(ILInitiative.entity_id == str(principal.user_id))
    if principal.school_id:
        q = q.where((ILInitiative.school_id == principal.school_id) | (ILInitiative.school_id.is_(None)))
    inits = list(db.execute(q.order_by(ILInitiative.created_at.desc())).scalars().all())
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
    require(principal, "intelligence.read", "intelligence", context={"allow_authenticated_school": True, "school_id": principal.school_id}, db=db)
    if principal.role in (Role.STUDENT, Role.PARENT) and str(principal.user_id) != entity_id:
        raise HTTPException(403, "forbidden")
    store = ILStore(db)
    q = select(ILInitiative).where(ILInitiative.entity_id == entity_id)
    if principal.school_id:
        q = q.where((ILInitiative.school_id == principal.school_id) | (ILInitiative.school_id.is_(None)))
    inits = list(db.execute(q.order_by(ILInitiative.created_at.desc())).scalars().all())
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
    require(principal, "intelligence.dismiss", "intelligence", context={"allow_authenticated_school": True, "school_id": principal.school_id}, db=db)
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
    require(principal, "intelligence.approve", "intelligence", context={"allow_authenticated_school": True, "school_id": principal.school_id}, db=db)
    if principal.role not in (Role.TEACHER, Role.LEADERSHIP):
        raise HTTPException(403, "forbidden")
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
    require(principal, "intelligence.read", "intelligence", context={"allow_authenticated_school": True, "school_id": principal.school_id}, db=db)
    store = ILStore(db)
    eff_role = role
    if principal.role in (Role.STUDENT, Role.PARENT, Role.TEACHER):
        eff_role = principal.role.value if hasattr(principal.role, 'value') else str(principal.role)
    items = store.list_communications(recipient_role=eff_role)
    if principal.role in (Role.STUDENT, Role.PARENT):
        items = [i for i in items if i.get('entity_id') == str(principal.user_id)]
    return {"items": items}


@router.post("/notifications/{comm_id}/acknowledge")
def acknowledge(comm_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    require(principal, "intelligence.ack", "intelligence", context={"allow_authenticated_school": True, "school_id": principal.school_id}, db=db)
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
    if principal.role != Role.LEADERSHIP:
        raise HTTPException(403, "forbidden")
    store = ILStore(db)
    items = store.list_audit(limit=limit)
    if principal.school_id:
        sid = str(principal.school_id)
        items = [i for i in items if i.get('school_id') in (None, sid)]
    return {"items": items}


# ---- admin/report parity ----

@router.get("/admin/config")
def admin_config(principal: Principal = Depends(get_current_principal)):
    if principal.role != Role.LEADERSHIP:
        raise HTTPException(403, "forbidden")
    return {
        "intelligence_enabled": K18_SETTINGS["INTELLIGENCE_ENABLED"],
        "retention_days_default": K18_SETTINGS["RETENTION_DAYS_DEFAULT"],
        "retention_approved": K18_SETTINGS["RETENTION_APPROVED"],
        "external_ai_allowed": K18_SETTINGS["EXTERNAL_AI_ALLOWED"],
        "human_approval_required_for_sensitive": K18_SETTINGS["HUMAN_APPROVAL_REQUIRED_FOR_SENSITIVE"],
        "max_notifications_per_entity_per_day": K18_SETTINGS["MAX_NOTIFICATIONS_PER_ENTITY_PER_DAY"],
    }


@router.get("/admin/health")
def admin_health(db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal.role != Role.LEADERSHIP:
        raise HTTPException(403, "forbidden")
    return {
        "ok": True,
        "db": {
            "events": db.execute(select(func.count(ILPerceptionEvent.id))).scalar() or 0,
            "initiatives": db.execute(select(func.count(ILInitiative.id))).scalar() or 0,
            "audit": db.execute(select(func.count(ILAudit.id))).scalar() or 0,
            "dead_letter": db.execute(select(func.count(ILDeadLetter.id))).scalar() or 0,
        },
    }


@router.get("/admin/entities")
def admin_entities(limit: int = 100, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal.role != Role.LEADERSHIP:
        raise HTTPException(403, "forbidden")
    q = select(ILInitiative.entity_id, ILInitiative.entity_type, func.count(ILInitiative.id), func.max(ILInitiative.created_at)).group_by(ILInitiative.entity_id, ILInitiative.entity_type).order_by(func.max(ILInitiative.created_at).desc()).limit(limit)
    rows = db.execute(q).all()
    return {"items": [{"entity_id": r[0], "entity_type": r[1], "n": r[2], "last_seen": r[3].isoformat() if r[3] else None} for r in rows]}


@router.get("/report/system")
def report_system(db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal.role != Role.LEADERSHIP:
        raise HTTPException(403, "forbidden")
    dup = db.execute(select(ILPerceptionEvent.event_id, func.count(ILPerceptionEvent.id)).group_by(ILPerceptionEvent.event_id).having(func.count(ILPerceptionEvent.id) > 1)).all()
    return {
        "counts": {
            "events": db.execute(select(func.count(ILPerceptionEvent.id))).scalar() or 0,
            "hypotheses": db.execute(select(func.count(ILHypothesis.id))).scalar() or 0,
            "predictions": db.execute(select(func.count(ILPrediction.id))).scalar() or 0,
            "initiatives": db.execute(select(func.count(ILInitiative.id))).scalar() or 0,
            "communications": db.execute(select(func.count(ILCommunication.id))).scalar() or 0,
            "outcomes": db.execute(select(func.count(ILOutcome.id))).scalar() or 0,
            "audit": db.execute(select(func.count(ILAudit.id))).scalar() or 0,
            "dead_letter": db.execute(select(func.count(ILDeadLetter.id))).scalar() or 0,
        },
        "invariants": {
            "all_hypotheses_have_entity": (db.execute(select(func.count(ILHypothesis.id)).where((ILHypothesis.entity_id == None) | (ILHypothesis.entity_id == ""))).scalar() or 0) == 0,  # noqa: E711
            "all_initiatives_have_entity": (db.execute(select(func.count(ILInitiative.id)).where((ILInitiative.entity_id == None) | (ILInitiative.entity_id == ""))).scalar() or 0) == 0,  # noqa: E711
            "no_duplicate_event_ids": len(dup) == 0,
        },
        "status": "INTEGRATED",
    }
