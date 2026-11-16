import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, String, Text, Uuid, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database.session import Base
from app.shared.types import Principal, new_uuid, utc_now


GENESIS_HASH = "0" * 64


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    principal_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    principal_role: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _ts_iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


def compute_record_hash(payload: dict[str, Any], prev_hash: str) -> str:
    data = {"prev_hash": prev_hash, **payload}
    return hashlib.sha256(_canonical(data).encode("utf-8")).hexdigest()


def _last_hash(db: Session) -> str:
    row = db.execute(
        select(AuditLog.record_hash).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).limit(1)
    ).scalar_one_or_none()
    return row or GENESIS_HASH


def write(
    db: Session,
    principal: Principal,
    action: str,
    resource: str,
    purpose: Optional[str],
    outcome: str,
    details: Optional[dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> AuditLog:
    ts = timestamp or utc_now()
    prev_hash = _last_hash(db)
    payload = {
        "timestamp": _ts_iso(ts),
        "principal_id": str(principal.user_id) if principal else None,
        "principal_role": principal.role.value if principal and principal.role else None,
        "school_id": str(principal.school_id) if principal and principal.school_id else None,
        "action": action,
        "resource": resource,
        "purpose": purpose,
        "outcome": outcome,
        "details": details or {},
    }
    record_hash = compute_record_hash(payload, prev_hash)
    entry = AuditLog(
        id=new_uuid(),
        timestamp=ts,
        principal_id=principal.user_id if principal else None,
        principal_role=principal.role.value if principal and principal.role else None,
        school_id=principal.school_id if principal and principal.school_id else None,
        action=action,
        resource=resource,
        purpose=purpose,
        outcome=outcome,
        details=_canonical(details or {}),
        prev_hash=prev_hash,
        record_hash=record_hash,
    )
    db.add(entry)
    db.flush()
    return entry


def verify_chain(db: Session) -> tuple[bool, Optional[str]]:
    rows = db.execute(select(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())).scalars().all()
    prev_hash = GENESIS_HASH
    for row in rows:
        payload = {
            "timestamp": _ts_iso(row.timestamp),
            "principal_id": str(row.principal_id) if row.principal_id else None,
            "principal_role": row.principal_role,
            "school_id": str(row.school_id) if row.school_id else None,
            "action": row.action,
            "resource": row.resource,
            "purpose": row.purpose,
            "outcome": row.outcome,
            "details": json.loads(row.details) if row.details else {},
        }
        expected = compute_record_hash(payload, prev_hash)
        if row.prev_hash != prev_hash or row.record_hash != expected:
            return False, str(row.id)
        prev_hash = row.record_hash
    return True, None
