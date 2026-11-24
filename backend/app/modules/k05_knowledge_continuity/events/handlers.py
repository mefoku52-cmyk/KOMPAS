from __future__ import annotations

import logging

from app.core.database.session import SessionLocal
from app.core.events.bus import DomainEvent, EventBus, current_session
from app.modules.k05_knowledge_continuity.domain.models import TopicProgressKind, TopicProgressStatus
from app.modules.k05_knowledge_continuity.services.service import K05Service
from app.shared.types import system_principal

logger = logging.getLogger(__name__)


def handle_answer_evaluated(event: DomainEvent) -> None:
    payload = event.payload or {}
    school_id = event.school_id or payload.get("school_id")
    student_user_id = payload.get("student_user_id")
    topic_id = payload.get("topic_id")
    if not (school_id and student_user_id and topic_id):
        return
    attempt_ref = payload.get("attempt_ref") or payload.get("attempt_id") or str(event.event_id)
    is_verification = bool(payload.get("is_verification", False))
    correct = bool(payload.get("correct", False))
    principal = system_principal()
    # Reuse the publishing transaction when there is one: a second connection
    # would read uncommitted state and hit the SQLite write lock.
    shared = current_session()
    db = shared if shared is not None else SessionLocal()
    owns_session = shared is None
    try:
        svc = K05Service(db)
        if is_verification and correct:
            kind = TopicProgressKind.VERIFIED
            status = TopicProgressStatus.VERIFIED_MASTERY
            ver_ev = True
        elif is_verification and not correct:
            kind = TopicProgressKind.VERIFIED
            status = TopicProgressStatus.PARTIALLY_MASTERED
            ver_ev = True
        else:
            # practice attempt never yields verified mastery
            kind = TopicProgressKind.PRACTICED
            status = TopicProgressStatus.IN_PROGRESS_PRACTICE if not correct else TopicProgressStatus.PARTIALLY_MASTERED
            ver_ev = False
        svc.record_state(
            principal,
            school_id=school_id,
            student_user_id=student_user_id,
            topic_id=topic_id,
            kind=kind,
            status=status,
            evidence_attempt_ref=str(attempt_ref),
            is_verification_evidence=ver_ev,
            purpose="answer_evaluated_event",
        )
        if owns_session:
            db.commit()
        else:
            db.flush()
    except Exception:
        db.rollback()
        logger.exception(
            "k05 handler failed for answer_evaluated",
            extra={"attempt_ref": str(attempt_ref), "topic_id": str(topic_id)},
        )
    finally:
        if owns_session:
            db.close()


def _handle_with_retry(event: DomainEvent, *, max_attempts: int = 3) -> None:
    """Retry only after handle_answer_evaluated has rolled back its failed transaction."""
    for attempt in range(1, max_attempts + 1):
        try:
            handle_answer_evaluated(event)
            return
        except Exception:
            if attempt >= max_attempts:
                logger.exception("k05 answer_evaluated retries exhausted", extra={"event_id": str(event.event_id)})
                raise
            logger.warning(
                "retrying k05 answer_evaluated handler",
                extra={"event_id": str(event.event_id), "attempt": attempt},
                exc_info=True,
            )


def register(bus: EventBus) -> None:
    bus.subscribe("learning.answer_evaluated", _handle_with_retry)
    bus.subscribe("AnswerEvaluated", _handle_with_retry)
