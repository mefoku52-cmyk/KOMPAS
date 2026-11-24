from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.modules.k14_communication_center.repository.repository import K14Repository
from app.shared.types import Principal


class K14Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K14Repository(db)

    def _require_participant(self, principal: Principal, thread_id: uuid.UUID, action: str, resource: str):
        thread = self.repo.get_thread(thread_id)
        if not thread:
            raise ValueError("thread_not_found")
        if principal.is_system:
            return thread
        if principal.school_id != thread.school_id or not self.repo.is_participant(thread_id, principal.user_id):
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": "not_participant"})
            raise PermissionError("not_participant")
        return thread

    def create_thread(self, principal: Principal, *, school_id: uuid.UUID, subject: str, participant_user_ids: list[uuid.UUID], is_private: bool = False, is_demo: bool = False):
        action = "k14.create_thread"
        if not principal.is_system and principal.school_id != school_id:
            audit_write(self.db, principal, action, f"communication_thread:school:{school_id}", None, "denied", {"reason": "wrong_school"})
            raise PermissionError("wrong_school")
        thread = self.repo.create_thread(school_id=school_id, subject=subject, is_private=is_private, created_by_user_id=principal.user_id, is_demo=is_demo)
        from app.shared.identity import User
        participants = set(participant_user_ids or [])
        if not principal.is_system:
            participants.add(principal.user_id)
        users = self.db.query(User).filter(User.id.in_(participants)).all() if participants else []
        valid_ids = {user.id for user in users if user.school_id == school_id and user.is_active}
        if valid_ids != participants:
            raise ValueError("participant_not_found_in_school")
        for uid in participants:
            self.repo.add_participant(school_id=school_id, thread_id=thread.id, user_id=uid, is_demo=is_demo)
        audit_write(self.db, principal, action, f"communication_thread:{thread.id}", None, "success", {"is_private": is_private, "participants": len(participants)})
        return thread

    def post_message(self, principal: Principal, *, thread_id: uuid.UUID, body: str, is_demo: bool = False):
        action = "k14.post_message"
        resource = f"communication_thread:{thread_id}"
        thread = self._require_participant(principal, thread_id, action, resource)
        msg = self.repo.add_message(school_id=thread.school_id, thread_id=thread.id, sender_user_id=principal.user_id, body=body, is_demo=is_demo)
        audit_write(self.db, principal, action, resource, None, "success", {"message_id": str(msg.id)})
        return msg

    def list_messages(self, principal: Principal, *, thread_id: uuid.UUID):
        action = "k14.read_messages"
        resource = f"communication_thread:{thread_id}"
        self._require_participant(principal, thread_id, action, resource)
        msgs = self.repo.list_messages(thread_id)
        # access to content is audited
        audit_write(self.db, principal, action, resource, None, "success", {"count": len(msgs)})
        return msgs

    def list_threads(self, principal: Principal, *, school_id: uuid.UUID):
        action = "k14.list_threads"
        resource = f"communication_thread:school:{school_id}"
        if principal.is_system:
            audit_write(self.db, principal, action, resource, None, "success", {"count": 0})
            return []
        if principal.school_id != school_id:
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": "wrong_school"})
            raise PermissionError("wrong_school")
        threads = self.repo.list_threads_for_user(school_id, principal.user_id)
        audit_write(self.db, principal, action, resource, None, "success", {"count": len(threads)})
        return threads
