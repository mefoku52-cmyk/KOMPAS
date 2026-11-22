from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.shared.types import utc_now
from .models import (
    ILPerceptionEvent, ILContextMemory, ILHypothesis, ILPrediction,
    ILInitiative, ILCommunication, ILOutcome, ILAudit,
)


class ILStore:
    def __init__(self, db: Session):
        self.db = db

    def audit(self, action: str, details: dict, actor: str = "system", entity_type: str | None = None, entity_id: str | None = None, school_id: uuid.UUID | None = None):
        rec = ILAudit(action=action, details=details or {}, actor=actor, entity_type=entity_type, entity_id=str(entity_id) if entity_id else None, school_id=school_id)
        self.db.add(rec)
        self.db.flush()
        return rec

    def get_event_by_event_id(self, event_id: uuid.UUID) -> ILPerceptionEvent | None:
        return self.db.execute(select(ILPerceptionEvent).where(ILPerceptionEvent.event_id == event_id)).scalar_one_or_none()

    def save_event(self, ev: dict) -> ILPerceptionEvent | None:
        existing = self.get_event_by_event_id(ev["event_id"])
        if existing:
            return None
        rec = ILPerceptionEvent(**ev)
        self.db.add(rec)
        self.db.flush()
        return rec

    def save_memory(self, m: dict) -> ILContextMemory:
        rec = ILContextMemory(**m)
        self.db.add(rec)
        self.db.flush()
        return rec

    def get_memory(self, entity_type: str, entity_id: str, limit: int = 20):
        stmt = select(ILContextMemory).where(ILContextMemory.entity_type == entity_type, ILContextMemory.entity_id == str(entity_id)).order_by(desc(ILContextMemory.created_at)).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def save_hypothesis(self, h: dict) -> ILHypothesis:
        rec = ILHypothesis(**h)
        self.db.add(rec)
        self.db.flush()
        return rec

    def save_prediction(self, p: dict) -> ILPrediction:
        rec = ILPrediction(**p)
        self.db.add(rec)
        self.db.flush()
        return rec

    def save_initiative(self, i: dict) -> ILInitiative:
        rec = ILInitiative(**i)
        self.db.add(rec)
        self.db.flush()
        return rec

    def update_initiative_status(self, init_id: uuid.UUID, status: str, actor: str | None = None):
        rec = self.db.get(ILInitiative, init_id)
        if not rec:
            return None
        rec.status = status
        if status in ("dismissed", "rejected", "approved", "executed", "closed"):
            rec.decided_at = utc_now()
            rec.decided_by = actor or "system"
        if status in ("dismissed", "rejected"):
            rec.dismissed_at = utc_now()
        self.db.flush()
        return rec

    def save_communication(self, c: dict) -> ILCommunication:
        rec = ILCommunication(**c)
        self.db.add(rec)
        self.db.flush()
        return rec

    def ack_communication(self, comm_id: uuid.UUID):
        rec = self.db.get(ILCommunication, comm_id)
        if not rec:
            return None
        rec.status = "acknowledged"
        rec.acknowledged_at = utc_now()
        self.db.flush()
        return rec

    def save_outcome(self, o: dict) -> ILOutcome:
        rec = ILOutcome(**o)
        self.db.add(rec)
        self.db.flush()
        return rec

    def list_events(self, limit=100):
        return list(self.db.execute(select(ILPerceptionEvent).order_by(desc(ILPerceptionEvent.created_at)).limit(limit)).scalars().all())

    def list_hypotheses(self, entity_id: str | None = None):
        stmt = select(ILHypothesis)
        if entity_id: stmt = stmt.where(ILHypothesis.entity_id == str(entity_id))
        return list(self.db.execute(stmt.order_by(desc(ILHypothesis.created_at)).limit(200)).scalars().all())

    def list_predictions(self, entity_id: str | None = None):
        stmt = select(ILPrediction)
        if entity_id: stmt = stmt.where(ILPrediction.entity_id == str(entity_id))
        return list(self.db.execute(stmt.order_by(desc(ILPrediction.created_at)).limit(200)).scalars().all())

    def list_initiatives(self, entity_id: str | None = None):
        stmt = select(ILInitiative)
        if entity_id: stmt = stmt.where(ILInitiative.entity_id == str(entity_id))
        return list(self.db.execute(stmt.order_by(desc(ILInitiative.created_at)).limit(200)).scalars().all())

    def list_communications(self, recipient_role: str | None = None):
        stmt = select(ILCommunication, ILInitiative).outerjoin(ILInitiative, ILCommunication.initiative_id == ILInitiative.id).order_by(desc(ILCommunication.sent_at)).limit(200)
        rs = []
        for c, i in self.db.execute(stmt).all():
            d = _to_dict(c)
            d["recipient_role"] = i.recipient_role if i else None
            d["entity_id"] = i.entity_id if i else None
            d["entity_type"] = i.entity_type if i else None
            if recipient_role and d.get("recipient_role") != recipient_role:
                continue
            rs.append(d)
        return rs

    def list_outcomes(self):
        return [_to_dict(r) for r in self.db.execute(select(ILOutcome).order_by(desc(ILOutcome.evaluated_at)).limit(200)).scalars().all()]

    def list_audit(self, limit=200):
        return [_to_dict(r) for r in self.db.execute(select(ILAudit).order_by(desc(ILAudit.ts)).limit(limit)).scalars().all()]

    def get_initiative(self, init_id: uuid.UUID):
        r = self.db.get(ILInitiative, init_id)
        return r

    def get_communication(self, comm_id: uuid.UUID):
        r = self.db.get(ILCommunication, comm_id)
        return r


def _to_dict(obj):
    if obj is None:
        return None
    d = {}
    for c in obj.__table__.columns:
        v = getattr(obj, c.name)
        if isinstance(v, uuid.UUID):
            v = str(v)
        elif hasattr(v, "isoformat"):
            try: v = v.isoformat()
            except Exception: pass
        d[c.name] = v
    return d
