from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k08_work_assistant.domain.models import DraftStatus
from app.modules.k08_work_assistant.repository.repository import K08Repository
from app.shared.types import Principal, Role


class K08Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K08Repository(db)

    def _owner_ctx(self, principal: Principal, school_id: uuid.UUID, teacher_user_id: uuid.UUID):
        if principal.is_system:
            return {"school_id": school_id, "system_internal": True}
        if principal.role == Role.TEACHER and principal.user_id == teacher_user_id:
            return {"scope": Scope.SELF.value, "owner_user_id": teacher_user_id, "school_id": school_id}
        return {"school_id": school_id}

    def _auth(self, principal: Principal, action: str, resource: str, context: dict):
        decision = authorize(principal, action, resource, context=context, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def _template_content(self, draft_type: str, title: str, topics: list[str] | None = None) -> str:
        topics = topics or []
        header = f"Navrh: {draft_type} - {title}"
        lines = [header, "", "Temy:"]
        for t in topics:
            lines.append(f"- {t}")
        if not topics:
            lines.append("- (bez specifikovanych tem)")
        lines.append("")
        lines.append("Obsah je sablonovy navrh a vyzaduje schvalenie ucitelom.")
        return "\n".join(lines)

    def generate_draft(
        self,
        principal: Principal,
        *,
        school_id: uuid.UUID,
        teacher_user_id: uuid.UUID,
        title: str,
        draft_type: str,
        topics: list[str] | None = None,
        use_orchestrator: bool = False,
        orchestrator=None,
        is_demo: bool = False,
    ):
        action = "k08.generate_draft"
        ctx = self._owner_ctx(principal, school_id, teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_assistant_draft:teacher:{teacher_user_id}", ctx)
        content = self._template_content(draft_type, title, topics)
        if use_orchestrator and orchestrator is not None:
            try:
                prompt = f"Vytvor {draft_type} '{title}' pre temy: {', '.join(topics or [])}"
                content = orchestrator.run(principal, task="work_assistant", prompt=prompt, payload={"topic_id": ",".join(topics or [])}, context={"system_internal": principal.is_system})
            except Exception:
                content = self._template_content(draft_type, title, topics)
        draft = self.repo.create_draft(school_id=school_id, teacher_user_id=teacher_user_id, title=title, draft_type=draft_type, content=content, source_refs=None, is_demo=is_demo)
        audit_write(self.db, principal, action, f"teacher_workspace_assistant_draft:{draft.id}", None, "success", {"used_orchestrator": use_orchestrator})
        return draft

    def submit_for_approval(self, principal: Principal, draft_id: uuid.UUID):
        action = "k08.submit_for_approval"
        draft = self.repo.get_draft(draft_id)
        if not draft:
            raise ValueError("draft_not_found")
        ctx = self._owner_ctx(principal, draft.school_id, draft.teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_assistant_draft:{draft.id}", ctx)
        if draft.status != DraftStatus.DRAFT.value:
            raise ValueError("invalid_status")
        draft = self.repo.set_status(draft, DraftStatus.SUBMITTED_FOR_APPROVAL)
        audit_write(self.db, principal, action, f"teacher_workspace_assistant_draft:{draft.id}", None, "success")
        return draft

    def approve(self, principal: Principal, draft_id: uuid.UUID):
        action = "k08.approve_draft"
        draft = self.repo.get_draft(draft_id)
        if not draft:
            raise ValueError("draft_not_found")
        ctx = self._owner_ctx(principal, draft.school_id, draft.teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_assistant_draft:{draft.id}", ctx)
        if draft.status != DraftStatus.SUBMITTED_FOR_APPROVAL.value:
            raise ValueError("invalid_status")
        draft = self.repo.set_status(draft, DraftStatus.APPROVED)
        audit_write(self.db, principal, action, f"teacher_workspace_assistant_draft:{draft.id}", None, "success")
        return draft

    def list_drafts(self, principal: Principal, *, school_id: uuid.UUID, teacher_user_id: uuid.UUID):
        action = "k08.list_drafts"
        ctx = self._owner_ctx(principal, school_id, teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_assistant_draft:teacher:{teacher_user_id}", ctx)
        rows = self.repo.list_for_teacher(school_id, teacher_user_id)
        audit_write(self.db, principal, action, f"teacher_workspace_assistant_draft:teacher:{teacher_user_id}", None, "success", {"count": len(rows)})
        return rows
