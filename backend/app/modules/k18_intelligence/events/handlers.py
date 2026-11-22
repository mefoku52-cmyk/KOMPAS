from __future__ import annotations

import logging
from app.core.events.bus import DomainEvent, current_session
from app.core.database.session import SessionLocal
from app.modules.k18_intelligence.services.orchestrator import IntelligenceOrchestrator

logger = logging.getLogger("kompas.k18")


def on_answer_evaluated(event: DomainEvent) -> None:
    payload = dict(event.payload or {})
    payload.setdefault("school_id", str(event.school_id) if event.school_id else None)
    payload.setdefault("entity_type", "student")
    payload.setdefault("entity_id", str(payload.get("student_user_id") or payload.get("student_id") or "unknown"))
    payload.setdefault("correct", payload.get("correct", payload.get("is_correct")))
    payload.setdefault("time_taken_sec", payload.get("time_taken_sec", payload.get("time", 999)))
    payload.setdefault("consecutive_errors", payload.get("consecutive_errors", 0))

    db = current_session()
    close = False
    if db is None:
        db = SessionLocal()
        close = True
    try:
        orch = IntelligenceOrchestrator(db)
        orch.process_event("mission_answer", payload, source="kompas:k04_missions", school_id=event.school_id, event_id=event.event_id)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("k18 AnswerEvaluated handler failed")
    finally:
        if close:
            db.close()


def register(bus) -> None:
    bus.subscribe("AnswerEvaluated", on_answer_evaluated)
