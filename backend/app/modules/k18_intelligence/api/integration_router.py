from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.shared.types import Principal, Role
from app.modules.k18_intelligence.services.orchestrator import IntelligenceOrchestrator
from app.modules.k18_intelligence.repository.store import ILStore, _to_dict
from app.modules.k18_intelligence.api.access import require_student_access, can_access_student

router = APIRouter(prefix="/integration", tags=["integration"])


class DomainEventIn(BaseModel):
    event_type: str
    event_id: Optional[str] = None
    source_module: str = "unknown"
    school_id: Optional[str] = None
    student_user_id: Optional[str] = None
    class_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: Optional[str] = None


@router.post("/events")
def ingest_domain_event(body: DomainEventIn, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if not principal:
        raise HTTPException(401, "auth required")
    payload = dict(body.payload)
    payload.setdefault("school_id", body.school_id or (str(principal.school_id) if principal.school_id else None))
    payload.setdefault("student_user_id", body.student_user_id)
    payload.setdefault("class_id", body.class_id)
    payload.setdefault("entity_type", body.entity_type or ("student" if body.student_user_id else "class" if body.class_id else "entity"))
    payload.setdefault("entity_id", body.entity_id or body.student_user_id or body.class_id or payload.get("student") or "unknown")
    if body.occurred_at:
        payload.setdefault("occurred_at", body.occurred_at)
    mapped = body.event_type
    if body.event_type == "AnswerEvaluated":
        mapped = "mission_answer"
        payload.setdefault("correct", payload.get("correct"))
        payload.setdefault("time_taken_sec", payload.get("time_taken_sec", payload.get("time", 999)))
    import uuid as _uuid
    eid = _uuid.UUID(body.event_id) if body.event_id else None
    orch = IntelligenceOrchestrator(db)
    res = orch.process_event(mapped, payload, source=f"kompas:{body.source_module}", school_id=payload.get("school_id"), event_id=eid)
    db.commit()
    return {"accepted": True, "mapped_event_type": mapped, "result": res}


def _student_safe(db: Session, student_id: str):
    store = ILStore(db)
    inits = store.list_initiatives(entity_id=student_id)
    preds = store.list_predictions(entity_id=student_id)
    comms = [c for c in store.list_communications() if c.get("entity_id") == student_id]
    notifications = [{"id": c["id"], "text": c.get("payload", {}).get("text"), "status": c["status"], "created_at": c.get("sent_at"), "content_key": c.get("content_key")} for c in comms]
    return {
        "student_id": student_id,
        "notifications": notifications,
        "support_signals_count": len([i for i in inits if getattr(i, "decision", None) in ("act", "request_more")]),
        "has_active_support": any(getattr(i, "status", None) in ("pending", "executed", "approved") for i in inits),
        "uncertainty": preds[0].uncertainty if preds else "unknown",
        "safe": True,
    }


@router.get("/students/{student_id}/summary")
def student_summary(student_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal.role != Role.LEADERSHIP:
        require_student_access(db, principal, student_id, action="k18.integration.student_summary")
    return _student_safe(db, student_id)


@router.get("/parents/{parent_id}/children/{student_id}/summary")
def parent_child_summary(parent_id: str, student_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal.role == Role.PARENT and str(principal.user_id) != parent_id:
        raise HTTPException(403, "forbidden")
    if principal.role != Role.LEADERSHIP:
        require_student_access(db, principal, student_id, action="k18.integration.parent_child_summary")
    data = _student_safe(db, student_id)
    data["parent_id"] = parent_id
    data["role"] = "parent"
    return data


@router.get("/teachers/{teacher_id}/overview")
def teacher_overview(teacher_id: str, class_id: Optional[str] = Query(None), db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal.role == Role.TEACHER and str(principal.user_id) != teacher_id:
        raise HTTPException(403, "forbidden")
    if principal.role not in (Role.TEACHER, Role.LEADERSHIP):
        raise HTTPException(403, "forbidden")
    store = ILStore(db)
    inits = store.list_initiatives()
    signals = []
    for i in inits:
        if not (i.recipient_role in ("teacher", None) or i.decision in ("act", "request_more")):
            continue
        if i.entity_type == "student" and principal.role == Role.TEACHER and not can_access_student(db, principal, i.entity_id):
            continue
        signals.append(_to_dict(i))
    comms = store.list_communications(recipient_role="teacher")
    if principal.role == Role.TEACHER:
        comms = [c for c in comms if c.get("entity_type") != "student" or can_access_student(db, principal, c.get("entity_id"))]
    return {"teacher_id": teacher_id, "class_id": class_id, "signals": signals, "notifications": comms}


@router.get("/health")
def health():
    return {"ok": True, "integration": "ready", "mode": "read-only-adapter"}

