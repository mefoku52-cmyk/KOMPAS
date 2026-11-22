"""K18 outbox/inbox simulation for main KOMPAS DB."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.shared.types import utc_now, new_uuid
from .models import ILDeadLetter
from sqlalchemy import String, Integer, DateTime, Text, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database.session import Base


class ILOutbox(Base):
    __tablename__ = "il_outbox"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ILInbox(Base):
    __tablename__ = "il_inbox"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    handler: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def enqueue_outbox(db: Session, event_id, event_type, payload):
    db.add(ILOutbox(event_id=event_id, event_type=event_type, payload=payload, status="pending"))
    db.flush()


def process_once(db: Session, orchestrator_factory, limit=20):
    items = list(db.execute(select(ILOutbox).where(ILOutbox.status.in_(["pending", "failed"]), ILOutbox.attempts < 3).order_by(ILOutbox.created_at).limit(limit)).scalars().all())
    processed = duplicates = failed = 0
    for it in items:
        it.status = "processing"
        db.flush()
        handler = "k18.orchestrator"
        seen = db.execute(select(ILInbox).where(ILInbox.event_id == it.event_id, ILInbox.handler == handler)).scalar_one_or_none()
        if seen and seen.status in ("done", "duplicate"):
            it.status = "done"; it.processed_at = utc_now(); duplicates += 1; continue
        try:
            orch = orchestrator_factory(db)
            res = orch.process_event(it.event_type, it.payload, source="outbox-worker", event_id=it.event_id, school_id=it.payload.get("school_id"))
            db.add(ILInbox(event_id=it.event_id, handler=handler, status="done" if res.get("status") != "duplicate" else "duplicate", attempts=1, processed_at=utc_now()))
            it.status = "done"; it.processed_at = utc_now(); processed += 1
        except Exception as e:
            it.attempts += 1; it.last_error = str(e)
            it.status = "dead_letter" if it.attempts >= 3 else "failed"
            db.add(ILInbox(event_id=it.event_id, handler=handler, status="failed", attempts=it.attempts, last_error=str(e)))
            if it.status == "dead_letter":
                db.add(ILDeadLetter(event_id=it.event_id, handler=handler, payload=it.payload, error=str(e), retry_count=it.attempts, last_attempt_at=utc_now(), school_id=None))
            failed += 1
    db.flush()
    return {"processed": processed, "duplicates": duplicates, "failed": failed, "claimed": len(items)}
