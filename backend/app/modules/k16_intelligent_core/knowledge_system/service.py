from __future__ import annotations

import re
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import authorize
from app.modules.k16_intelligent_core.repository.repository import K16Repository
from app.shared.types import Principal


class KnowledgeIndex:
    """Keyword search over approved documents (default, per D4)."""

    def search(self, query: str, texts: list[tuple[object, str]], limit: int = 10):
        q_tokens = {t for t in re.findall(r"\w+", query.lower()) if t}
        if not q_tokens:
            return []
        scored = []
        for obj, text in texts:
            tokens = re.findall(r"\w+", (text or "").lower())
            score = sum(1 for t in tokens if t in q_tokens)
            if score > 0:
                scored.append((score, obj))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [obj for _, obj in scored[:limit]]


class KnowledgeSystemService:
    def __init__(self, db: Session, index: Optional[KnowledgeIndex] = None):
        self.db = db
        self.repo = K16Repository(db)
        self.index = index or KnowledgeIndex()

    def register_source(
        self,
        principal: Principal,
        school_id: uuid.UUID,
        name: str,
        source_type: str,
        content: str,
        approved: bool = False,
    ):
        decision = authorize(principal, "ai.register_source", "ai_knowledge_source", context={"school_id": school_id, "system_internal": principal.is_system})
        if not decision.allowed:
            audit_write(self.db, principal, "ai.register_source", f"school:{school_id}", None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        obj = self.repo.create_source(school_id=school_id, name=name, source_type=source_type, content=content, approved=approved)
        audit_write(self.db, principal, "ai.register_source", f"ai_knowledge_source:{obj.id}", None, "success")
        return obj

    def search_approved(self, principal: Principal, school_id: uuid.UUID, query: str):
        decision = authorize(principal, "ai.search_knowledge", "ai_knowledge_source", context={"school_id": school_id, "system_internal": principal.is_system})
        if not decision.allowed:
            audit_write(self.db, principal, "ai.search_knowledge", f"school:{school_id}", None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        sources = self.repo.list_approved_sources(school_id)
        results = self.index.search(query, [(s, f"{s.name}\n{s.content}") for s in sources])
        audit_write(self.db, principal, "ai.search_knowledge", f"school:{school_id}", None, "success", {"query": query, "count": len(results)})
        return results
