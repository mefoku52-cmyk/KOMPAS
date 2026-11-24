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
from app.modules.k18_intelligence.api.access import require_student_access, require_leadership, filter_initiatives_for_principal, can_access_student

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
    if principal is None:
        raise HTTPException(401, "auth required")
    if principal.is_system:
        pass
    elif principal.role not in (Role.TEACHER, Role.LEADERSHIP):
        raise HTTPException(403, "event_ingest_forbidden")
    if body.event_type not in {"teacher_note", "conflict_report"}:
        raise HTTPException(403, "event_type_not_allowed")
    target = body.payload.get("entity_id") or body.payload.get("student_user_id") or body.payload.get("student")
    if not target:
        raise HTTPException(400, "event_entity_required")
    from app.modules.k18_intelligence.api.access import can_access_entity
    entity_type = body.payload.get("entity_type", "student")
    if not principal.is_system and not can_access_entity(db, principal, entity_type, str(target)):
        raise HTTPException(403, "event_entity_forbidden")
    import uuid as _uuid
    try:
        target_school = _uuid.UUID(body.school_id) if body.school_id else principal.school_id
    except ValueError as exc:
        raise HTTPException(400, "invalid_school_id") from exc
    if not principal.is_system and target_school != principal.school_id:
        raise HTTPException(403, "event_school_forbidden")
    orch = IntelligenceOrchestrator(db)
    eid = _uuid.UUID(body.event_id) if body.event_id else None
    school_id = str(target_school) if target_school else None
    res = orch.process_event(body.event_type, body.payload, source=body.source, school_id=school_id, event_id=eid, locale=body.locale)
    ILStore(db).audit("intelligence.ingest", {"event_type": body.event_type, "event_id": str(eid) if eid else None, "status": res.get("status")}, actor=str(principal.user_id), school_id=principal.school_id)
    db.commit()
    return res


@router.get("/situations")
def situations(entity_id: Optional[str] = None, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal is None:
        raise HTTPException(401, "auth required")
    store = ILStore(db)
    if entity_id and principal.role in (Role.STUDENT, Role.PARENT, Role.TEACHER):
        # validate access to requested entity
        if not (principal.role in (Role.STUDENT, Role.PARENT) and str(principal.user_id) == entity_id):
            require_student_access(db, principal, entity_id, action="k18.situations.read")
    q = select(ILInitiative)
    if entity_id:
        q = q.where(ILInitiative.entity_id == entity_id)
    if principal.school_id:
        q = q.where((ILInitiative.school_id == principal.school_id) | (ILInitiative.school_id.is_(None)))
    inits = list(db.execute(q.order_by(ILInitiative.created_at.desc())).scalars().all())
    inits = filter_initiatives_for_principal(db, principal, inits)
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
    if principal is None:
        raise HTTPException(401, "auth required")
    if principal.role != Role.LEADERSHIP:
        require_student_access(db, principal, entity_id, action="k18.situation_detail.read")
    store = ILStore(db)
    q = select(ILInitiative).where(ILInitiative.entity_id == entity_id)
    if principal.school_id:
        q = q.where((ILInitiative.school_id == principal.school_id) | (ILInitiative.school_id.is_(None)))
    inits = list(db.execute(q.order_by(ILInitiative.created_at.desc())).scalars().all())
    inits = filter_initiatives_for_principal(db, principal, inits)
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
    if principal is None:
        raise HTTPException(401, "auth required")
    import uuid as _uuid
    try: iid = _uuid.UUID(initiative_id)
    except ValueError: raise HTTPException(400, "invalid initiative_id")
    store = ILStore(db)
    init = store.get_initiative(iid)
    if not init:
        raise HTTPException(404, "initiative not found")
    # leadership can dismiss; teacher only for students they teach / same school signals; student/parent no
    if principal.role == Role.LEADERSHIP:
        pass
    elif principal.role == Role.TEACHER and init.entity_type == "student":
        require_student_access(db, principal, init.entity_id, action="k18.dismiss")
    else:
        raise HTTPException(403, "forbidden")
    store.update_initiative_status(init.id, "dismissed", actor=str(principal.user_id))
    store.audit("situation.dismissed", {"reason": body.reason, "note": body.note, "decision_reason": "teacher_or_leadership_dismiss"}, actor=str(principal.user_id), entity_type="initiative", entity_id=str(init.id), school_id=principal.school_id)
    db.commit()
    return {"id": str(init.id), "status": "dismissed"}


@router.post("/situations/{initiative_id}/approve")
def approve(initiative_id: str, body: ApproveIn, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal is None:
        raise HTTPException(401, "auth required")
    if principal.role not in (Role.TEACHER, Role.LEADERSHIP):
        raise HTTPException(403, "forbidden")
    import uuid as _uuid
    try: iid = _uuid.UUID(initiative_id)
    except ValueError: raise HTTPException(400, "invalid initiative_id")
    store = ILStore(db)
    init = store.get_initiative(iid)
    if not init:
        raise HTTPException(404, "initiative not found")
    if principal.school_id != init.school_id:
        raise HTTPException(403, "initiative_school_forbidden")
    if principal.role == Role.TEACHER and init.entity_type == "student":
        require_student_access(db, principal, init.entity_id, action="k18.approve")
    status_val = "approved" if body.approved else "rejected"
    store.update_initiative_status(init.id, status_val, actor=str(principal.user_id))
    if body.approved:
        from app.modules.k18_intelligence.services.safety.service import SafetyGovernance
        from app.modules.k18_intelligence.services.communication.service import CommunicationEngine
        CommunicationEngine(store, SafetyGovernance(), db).compose_and_send(store.get_initiative(init.id))
    store.audit("initiative.approval", {"approved": body.approved, "note": body.note, "decision_reason": "human_approval"}, actor=str(principal.user_id), entity_type="initiative", entity_id=str(init.id), school_id=principal.school_id)
    db.commit()
    return {"id": str(init.id), "status": status_val}


@router.get("/notifications")
def notifications(role: Optional[str] = None, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal is None:
        raise HTTPException(401, "auth required")
    store = ILStore(db)
    eff_role = role
    if principal.role in (Role.STUDENT, Role.PARENT, Role.TEACHER):
        eff_role = principal.role.value if hasattr(principal.role, 'value') else str(principal.role)
    items = store.list_communications(recipient_role=eff_role)
    if principal.role in (Role.STUDENT, Role.PARENT):
        items = [i for i in items if i.get('entity_id') == str(principal.user_id)]
    elif principal.role == Role.TEACHER:
        items = [i for i in items if i.get('entity_type') != 'student' or can_access_student(db, principal, i.get('entity_id'))]
    return {"items": items}


@router.post("/notifications/{comm_id}/acknowledge")
def acknowledge(comm_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal is None:
        raise HTTPException(401, "auth required")
    import uuid as _uuid
    try: cid = _uuid.UUID(comm_id)
    except ValueError: raise HTTPException(400, "invalid communication_id")
    store = ILStore(db)
    comm = store.get_communication(cid)
    if not comm:
        raise HTTPException(404, "notification not found")
    # check entity access if linked via initiative
    init = store.get_initiative(comm.initiative_id) if comm.initiative_id else None
    if init and init.entity_type == "student" and principal.role in (Role.STUDENT, Role.PARENT, Role.TEACHER):
        if principal.role in (Role.STUDENT, Role.PARENT) and str(principal.user_id) != init.entity_id:
            raise HTTPException(403, "forbidden")
        if principal.role == Role.TEACHER:
            require_student_access(db, principal, init.entity_id, action="k18.ack")
    store.ack_communication(comm.id)
    store.audit("notification.ack", {"communication_id": str(comm.id)}, actor=str(principal.user_id), entity_type="communication", entity_id=str(comm.id), school_id=principal.school_id)
    db.commit()
    return {"id": str(comm.id), "status": "acknowledged"}


@router.get("/audit")
def audit(limit: int = 200, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    require_leadership(db, principal, action="k18.audit.read")
    store = ILStore(db)
    items = store.list_audit(limit=limit)
    if principal.school_id:
        sid = str(principal.school_id)
        items = [i for i in items if i.get('school_id') in (None, sid)]
    return {"items": items}


# ---- admin/report parity ----

@router.get("/admin/config")
def admin_config(db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    require_leadership(db, principal, action="k18.admin.config")
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
    require_leadership(db, principal, action="k18.admin.health")
    return {
        "ok": True,
        "db": {
            "events": db.execute(select(func.count(ILPerceptionEvent.id)).where(ILPerceptionEvent.school_id == principal.school_id)).scalar() or 0,
            "initiatives": db.execute(select(func.count(ILInitiative.id)).where(ILInitiative.school_id == principal.school_id)).scalar() or 0,
            "audit": db.execute(select(func.count(ILAudit.id)).where(ILAudit.school_id == principal.school_id)).scalar() or 0,
            "dead_letter": db.execute(select(func.count(ILDeadLetter.id)).where(ILDeadLetter.school_id == principal.school_id)).scalar() or 0,
        },
    }


@router.get("/admin/entities")
def admin_entities(limit: int = 100, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    require_leadership(db, principal, action="k18.admin.entities")
    q = select(ILInitiative.entity_id, ILInitiative.entity_type, func.count(ILInitiative.id), func.max(ILInitiative.created_at))
    if principal.school_id:
        q = q.where(ILInitiative.school_id == principal.school_id)
    q = q.group_by(ILInitiative.entity_id, ILInitiative.entity_type).order_by(func.max(ILInitiative.created_at).desc()).limit(max(1, min(limit, 500)))
    rows = db.execute(q).all()
    return {"items": [{"entity_id": r[0], "entity_type": r[1], "n": r[2], "last_seen": r[3].isoformat() if r[3] else None} for r in rows]}


@router.get("/report/system")
def report_system(db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    require_leadership(db, principal, action="k18.report.system")
    school_filter = ILPerceptionEvent.school_id == principal.school_id if principal.school_id else ILPerceptionEvent.school_id.is_(None)
    initiative_filter = ILInitiative.school_id == principal.school_id if principal.school_id else ILInitiative.school_id.is_(None)
    dup = db.execute(select(ILPerceptionEvent.event_id, func.count(ILPerceptionEvent.id)).where(school_filter).group_by(ILPerceptionEvent.event_id).having(func.count(ILPerceptionEvent.id) > 1)).all()
    return {
        "counts": {
            "events": db.execute(select(func.count(ILPerceptionEvent.id)).where(school_filter)).scalar() or 0,
            "hypotheses": db.execute(select(func.count(ILHypothesis.id)).where(ILHypothesis.school_id == principal.school_id)).scalar() or 0,
            "predictions": db.execute(select(func.count(ILPrediction.id)).where(ILPrediction.school_id == principal.school_id)).scalar() or 0,
            "initiatives": db.execute(select(func.count(ILInitiative.id)).where(initiative_filter)).scalar() or 0,
            "communications": db.execute(select(func.count(ILCommunication.id)).where(ILCommunication.school_id == principal.school_id)).scalar() or 0,
            "outcomes": db.execute(select(func.count(ILOutcome.id)).where(ILOutcome.school_id == principal.school_id)).scalar() or 0,
            "audit": db.execute(select(func.count(ILAudit.id)).where(ILAudit.school_id == principal.school_id)).scalar() or 0,
            "dead_letter": db.execute(select(func.count(ILDeadLetter.id)).where(ILDeadLetter.school_id == principal.school_id)).scalar() or 0,
        },
        "invariants": {
            "all_hypotheses_have_entity": (db.execute(select(func.count(ILHypothesis.id)).where((ILHypothesis.entity_id == None) | (ILHypothesis.entity_id == ""))).scalar() or 0) == 0,  # noqa: E711
            "all_initiatives_have_entity": (db.execute(select(func.count(ILInitiative.id)).where((ILInitiative.entity_id == None) | (ILInitiative.entity_id == ""))).scalar() or 0) == 0,  # noqa: E711
            "no_duplicate_event_ids": len(dup) == 0,
        },
        "status": "INTEGRATED",
    }
