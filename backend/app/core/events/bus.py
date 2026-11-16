from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database.session import Base, SessionLocal
from app.shared.types import new_uuid, utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    school_id: Optional[uuid.UUID]
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: uuid.UUID = field(default_factory=new_uuid)
    occurred_at: datetime = field(default_factory=utc_now)


class EventLog(Base):
    __tablename__ = "audit_event_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Handler = Callable[[DomainEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent, db: Optional[Session] = None) -> None:
        self._persist(event, db)
        for handler in list(self._handlers.get(event.event_type, [])):
            try:
                handler(event)
            except Exception:
                logger.exception("event handler failed", extra={"event_type": event.event_type, "event_id": str(event.event_id)})

    def _persist(self, event: DomainEvent, db: Optional[Session]) -> None:
        import json

        record = EventLog(
            id=event.event_id,
            event_type=event.event_type,
            school_id=event.school_id,
            payload=json.dumps(event.payload, sort_keys=True, default=str),
            occurred_at=event.occurred_at,
        )
        if db is not None:
            db.add(record)
            db.flush()
        else:
            session = SessionLocal()
            try:
                session.add(record)
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("event log persist failed", extra={"event_id": str(event.event_id)})
            finally:
                session.close()


bus = EventBus()
