from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k11_operations_center.domain.models import OperationRequest


class K11Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, *, school_id: uuid.UUID, requester_user_id: uuid.UUID, request_type: str, title: str, description: str | None = None, status: str = "submitted", is_demo: bool = False) -> OperationRequest:
        obj = OperationRequest(school_id=school_id, requester_user_id=requester_user_id, request_type=request_type, title=title, description=description, status=status, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_request(self, request_id: uuid.UUID) -> OperationRequest | None:
        return self.db.get(OperationRequest, request_id)

    def list_requests(self, school_id: uuid.UUID):
        stmt = select(OperationRequest).where(OperationRequest.school_id == school_id)
        return list(self.db.execute(stmt).scalars().all())
