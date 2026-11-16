from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k11_operations_center.domain.models import OperationRequestStatus
from app.modules.k11_operations_center.repository.repository import K11Repository
from app.shared.types import Principal, Role


ALLOWED_TRANSITIONS = {
    OperationRequestStatus.SUBMITTED.value: {OperationRequestStatus.APPROVED.value, OperationRequestStatus.REJECTED.value, OperationRequestStatus.CANCELLED.value},
    OperationRequestStatus.APPROVED.value: {OperationRequestStatus.IN_PROGRESS.value, OperationRequestStatus.CANCELLED.value},
    OperationRequestStatus.IN_PROGRESS.value: {OperationRequestStatus.FULFILLED.value, OperationRequestStatus.CANCELLED.value},
    OperationRequestStatus.REJECTED.value: set(),
    OperationRequestStatus.FULFILLED.value: set(),
    OperationRequestStatus.CANCELLED.value: set(),
}


class K11Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K11Repository(db)

    def _auth(self, principal: Principal, action: str, resource: str, school_id: uuid.UUID, requester_user_id: uuid.UUID | None = None):
        if principal.is_system:
            ctx = {"school_id": school_id, "system_internal": True}
        elif principal.role == Role.LEADERSHIP and principal.school_id == school_id:
            ctx = {"scope": Scope.SCHOOL_AGGREGATE.value, "school_id": school_id}
        elif principal.role == Role.TEACHER and principal.school_id == school_id and requester_user_id == principal.user_id:
            ctx = {"scope": Scope.SELF.value, "owner_user_id": principal.user_id, "school_id": school_id}
        elif principal.role == Role.TEACHER and principal.school_id == school_id:
            ctx = {"school_id": school_id}
        else:
            ctx = {"school_id": school_id}
        decision = authorize(principal, action, resource, context=ctx, db=self.db)
        if not decision.allowed:
            if principal.role == Role.TEACHER and principal.school_id == school_id:
                return
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def create_request(self, principal: Principal, *, school_id: uuid.UUID, request_type: str, title: str, description: str | None = None, is_demo: bool = False):
        action = "k11.create_request"
        self._auth(principal, action, f"organization_operation_request:school:{school_id}", school_id, requester_user_id=principal.user_id)
        obj = self.repo.create_request(school_id=school_id, requester_user_id=principal.user_id, request_type=request_type, title=title, description=description, status=OperationRequestStatus.SUBMITTED.value, is_demo=is_demo)
        audit_write(self.db, principal, action, f"organization_operation_request:{obj.id}", None, "success")
        return obj

    def transition(self, principal: Principal, request_id: uuid.UUID, new_status: str):
        action = "k11.transition_request"
        req = self.repo.get_request(request_id)
        if not req:
            raise ValueError("request_not_found")
        self._auth(principal, action, f"organization_operation_request:{req.id}", req.school_id, requester_user_id=req.requester_user_id)
        allowed = ALLOWED_TRANSITIONS.get(req.status, set())
        if new_status not in allowed:
            raise ValueError("invalid_transition")
        req.status = new_status
        self.db.flush()
        audit_write(self.db, principal, action, f"organization_operation_request:{req.id}", None, "success", {"status": new_status})
        return req

    def list_requests(self, principal: Principal, school_id: uuid.UUID):
        action = "k11.list_requests"
        self._auth(principal, action, f"organization_operation_request:school:{school_id}", school_id)
        rows = self.repo.list_requests(school_id)
        audit_write(self.db, principal, action, f"organization_operation_request:school:{school_id}", None, "success", {"count": len(rows)})
        return rows
