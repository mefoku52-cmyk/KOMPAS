from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k16_intelligent_core.repository.repository import K16Repository
from app.shared.types import Principal, Role


class ContextMemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K16Repository(db)

    def add_record(self, principal: Principal, school_id: uuid.UUID, source_record_ref: str, content: str):
        if not source_record_ref or not source_record_ref.strip():
            raise ValueError("source_record_ref required")
        context = {"school_id": school_id, "system_internal": principal.is_system}
        if principal.role == Role.LEADERSHIP and principal.school_id == school_id:
            context = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": school_id}
        decision = authorize(principal, "ai.write_context_memory", "ai_knowledge_context_memory", context=context)
        if not decision.allowed:
            audit_write(self.db, principal, "ai.write_context_memory", f"school:{school_id}", None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        obj = self.repo.create_context_memory(school_id=school_id, source_record_ref=source_record_ref, content=content)
        audit_write(self.db, principal, "ai.write_context_memory", f"ai_knowledge_context_memory:{obj.id}", None, "success", {"source_record_ref": source_record_ref})
        return obj

    def list_records(self, principal: Principal, school_id: uuid.UUID):
        context = {"school_id": school_id, "system_internal": principal.is_system}
        if principal.role == Role.LEADERSHIP and principal.school_id == school_id:
            context = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": school_id}
        decision = authorize(principal, "ai.read_context_memory", "ai_knowledge_context_memory", context=context)
        if not decision.allowed:
            audit_write(self.db, principal, "ai.read_context_memory", f"school:{school_id}", None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        rows = self.repo.list_context_memories(school_id)
        audit_write(self.db, principal, "ai.read_context_memory", f"school:{school_id}", None, "success", {"count": len(rows)})
        return rows
