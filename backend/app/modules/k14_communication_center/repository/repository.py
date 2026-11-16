from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k14_communication_center.domain.models import CommunicationMessage, CommunicationParticipant, CommunicationThread


class K14Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_thread(self, *, school_id: uuid.UUID, subject: str, is_private: bool, created_by_user_id: uuid.UUID, is_demo: bool = False) -> CommunicationThread:
        t = CommunicationThread(school_id=school_id, subject=subject, is_private=is_private, created_by_user_id=created_by_user_id, is_demo=is_demo)
        self.db.add(t)
        self.db.flush()
        return t

    def add_participant(self, *, school_id: uuid.UUID, thread_id: uuid.UUID, user_id: uuid.UUID, is_demo: bool = False) -> CommunicationParticipant:
        p = CommunicationParticipant(school_id=school_id, thread_id=thread_id, user_id=user_id, is_demo=is_demo)
        self.db.add(p)
        self.db.flush()
        return p

    def get_thread(self, thread_id: uuid.UUID) -> CommunicationThread | None:
        return self.db.get(CommunicationThread, thread_id)

    def is_participant(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(CommunicationParticipant.id).where(CommunicationParticipant.thread_id == thread_id, CommunicationParticipant.user_id == user_id)
        return self.db.execute(stmt).first() is not None

    def list_threads_for_user(self, school_id: uuid.UUID, user_id: uuid.UUID) -> list[CommunicationThread]:
        stmt = (
            select(CommunicationThread)
            .join(CommunicationParticipant, CommunicationParticipant.thread_id == CommunicationThread.id)
            .where(CommunicationThread.school_id == school_id, CommunicationParticipant.user_id == user_id)
            .distinct()
        )
        return list(self.db.execute(stmt).scalars().all())

    def add_message(self, *, school_id: uuid.UUID, thread_id: uuid.UUID, sender_user_id: uuid.UUID, body: str, is_demo: bool = False) -> CommunicationMessage:
        m = CommunicationMessage(school_id=school_id, thread_id=thread_id, sender_user_id=sender_user_id, body=body, is_demo=is_demo)
        self.db.add(m)
        self.db.flush()
        return m

    def list_messages(self, thread_id: uuid.UUID) -> list[CommunicationMessage]:
        stmt = select(CommunicationMessage).where(CommunicationMessage.thread_id == thread_id).order_by(CommunicationMessage.valid_from.asc())
        return list(self.db.execute(stmt).scalars().all())
