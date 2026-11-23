from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid, utc_now


class SISProviderType(str, enum.Enum):
    EDUPAGE = "edupage"


class SISJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SISJobMode(str, enum.Enum):
    FULL = "full"
    DELTA = "delta"
    DRY_RUN = "dry_run"


class SISConflictState(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class SISSource(Base, ValidityMixin):
    __tablename__ = "sis_source"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(32), nullable=False, default=SISProviderType.EDUPAGE.value)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    secret_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    encrypted_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_cursor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("school_id", "provider_type", "name", name="uq_sis_source_school_provider_name"),
    )


class SISIdentityMap(Base, ValidityMixin):
    __tablename__ = "sis_identity_map"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sis_source.id"), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    internal_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    external_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    payload_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    absent_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflict_state: Mapped[str] = mapped_column(String(32), nullable=False, default=SISConflictState.RESOLVED.value)
    conflict_detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("source_id", "entity_type", "external_id", name="uq_sis_identity_source_entity_external"),
    )


class SISSyncJob(Base, ValidityMixin):
    __tablename__ = "sis_sync_job"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sis_source.id"), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default=SISJobMode.FULL.value)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SISJobStatus.PENDING.value)
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("identity_user.id"), nullable=True, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SISSyncItem(Base, ValidityMixin):
    __tablename__ = "sis_sync_item"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sis_sync_job.id"), nullable=False, index=True)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sis_source.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    internal_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
