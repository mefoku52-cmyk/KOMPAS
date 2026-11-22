from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.shared.types import Principal
from app.modules.k18_intelligence.repository.outbox import ILOutbox, ILInbox, enqueue_outbox, process_once
from app.modules.k18_intelligence.services.orchestrator import IntelligenceOrchestrator
from app.modules.k18_intelligence.repository.models import ILDeadLetter

router = APIRouter(prefix="/intelligence/ops", tags=["intelligence-ops"])

@router.post("/outbox/enqueue")
def enqueue(event_id: str, event_type: str, payload: dict, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    import uuid as _uuid
    enqueue_outbox(db, _uuid.UUID(event_id), event_type, payload)
    db.commit()
    return {"ok": True}

@router.post("/process-once")
def run_once(limit: int = 20, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    res = process_once(db, lambda db: IntelligenceOrchestrator(db), limit=limit)
    db.commit()
    return res

@router.get("/queues")
def queues(db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    def cnt(model):
        rows = db.execute(select(model.status, func.count(model.id)).group_by(model.status)).all()
        return [{"status": s, "c": c} for s, c in rows]
    dlq = db.execute(select(func.count(ILDeadLetter.id))).scalar() or 0
    return {"outbox": cnt(ILOutbox), "inbox": cnt(ILInbox), "dead_letter": dlq}
